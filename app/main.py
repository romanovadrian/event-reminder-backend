import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.auth.dependencies import get_current_user
from app.auth.schemas import LogoutResponse, TokenResponse
from app.auth.security import create_access_token, hash_password, verify_password
from app.database import Base, engine, get_db
from app.models import User
from app.schemas import (
    ReminderAssignmentCreate,
    ReminderAssignmentRead,
    UserAdminCreate,
    ReminderCreate,
    ReminderRead,
    ReminderUpdate,
    UserCreate,
    UserRead,
)
from app.services.scheduler import get_poll_interval, scheduler

logging.basicConfig(level=logging.INFO)


def _run_scheduler_tick() -> None:
    scheduler.run_once()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    from asyncio import create_task, sleep

    stop = False

    async def polling_loop() -> None:
        while not stop:
            _run_scheduler_tick()
            await sleep(get_poll_interval())

    task = create_task(polling_loop())
    try:
        yield
    finally:
        stop = True
        task.cancel()


app = FastAPI(title="Event Reminder API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    existing = crud.get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    return crud.create_registered_user(db, payload, hashed_password=hash_password(payload.password))


@app.post("/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    user = crud.get_user_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token)


@app.post("/auth/logout", response_model=LogoutResponse)
def logout(current_user: User = Depends(get_current_user)) -> LogoutResponse:
    return LogoutResponse(message=f"Logged out user {current_user.email}. Discard bearer token on client.")


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    payload: UserAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    _ = current_user
    existing = crud.get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Admin-created users receive a temporary randomized password hash placeholder.
    temporary_password = str(uuid.uuid4())
    return crud.create_user_admin(db, payload, hashed_password=hash_password(temporary_password))


@app.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[UserRead]:
    _ = current_user
    return crud.list_users(db)


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> UserRead:
    _ = current_user
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/reminders", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderRead:
    _ = current_user
    return crud.create_reminder(db, payload)


@app.get("/reminders", response_model=list[ReminderRead])
def list_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ReminderRead]:
    _ = current_user
    return crud.list_reminders(db)


@app.get("/reminders/{reminder_id}", response_model=ReminderRead)
def get_reminder(
    reminder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderRead:
    _ = current_user
    reminder = crud.get_reminder(db, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    return reminder


@app.patch("/reminders/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: uuid.UUID,
    payload: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderRead:
    _ = current_user
    reminder = crud.get_reminder(db, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    return crud.update_reminder(db, reminder, payload)


@app.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    _ = current_user
    reminder = crud.get_reminder(db, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    crud.delete_reminder(db, reminder)


@app.post("/reminders/{reminder_id}/users", response_model=ReminderAssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_user_to_reminder(
    reminder_id: uuid.UUID,
    payload: ReminderAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderAssignmentRead:
    _ = current_user
    reminder = crud.get_reminder(db, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    user = crud.get_user(db, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return crud.assign_user_to_reminder(db, reminder, payload)


@app.get("/reminders/{reminder_id}/users", response_model=list[ReminderAssignmentRead])
def list_reminder_users(
    reminder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReminderAssignmentRead]:
    _ = current_user
    reminder = crud.get_reminder(db, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    return crud.list_reminder_assignments(db, reminder_id)


@app.delete("/reminders/{reminder_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_user_from_reminder(
    reminder_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    _ = current_user
    reminder = crud.get_reminder(db, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    removed = crud.remove_user_assignment(db, reminder_id, user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder assignment not found")
