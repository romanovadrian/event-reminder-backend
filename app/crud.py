import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Reminder, ReminderUser, User
from app.schemas import ReminderAssignmentCreate, ReminderCreate, ReminderUpdate, UserAdminCreate, UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    raise NotImplementedError("Use create_registered_user or create_user_admin")


def create_registered_user(db: Session, payload: UserCreate, hashed_password: str) -> User:
    user_data = payload.model_dump(exclude={"password"})
    user = User(**user_data, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_user_admin(db: Session, payload: UserAdminCreate, hashed_password: str) -> User:
    user = User(**payload.model_dump(), hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    stmt = select(User).order_by(User.created_at.asc())
    return list(db.scalars(stmt).all())


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def create_reminder(db: Session, payload: ReminderCreate) -> Reminder:
    reminder = Reminder(**payload.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def list_reminders(db: Session) -> list[Reminder]:
    stmt = (
        select(Reminder)
        .options(joinedload(Reminder.user_links).joinedload(ReminderUser.user))
        .order_by(Reminder.event_date.asc())
    )
    return list(db.execute(stmt).unique().scalars().all())


def get_reminder(db: Session, reminder_id: uuid.UUID) -> Reminder | None:
    stmt = (
        select(Reminder)
        .where(Reminder.id == reminder_id)
        .options(joinedload(Reminder.user_links).joinedload(ReminderUser.user))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def update_reminder(db: Session, reminder: Reminder, payload: ReminderUpdate) -> Reminder:
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(reminder, key, value)

    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder: Reminder) -> None:
    db.delete(reminder)
    db.commit()


def assign_user_to_reminder(db: Session, reminder: Reminder, payload: ReminderAssignmentCreate) -> ReminderUser:
    existing = db.execute(
        select(ReminderUser).where(ReminderUser.reminder_id == reminder.id, ReminderUser.user_id == payload.user_id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    assignment = ReminderUser(reminder_id=reminder.id, user_id=payload.user_id, notify_time=payload.notify_time)
    db.add(assignment)
    db.commit()
    refreshed = (
        db.execute(
            select(ReminderUser)
            .where(ReminderUser.id == assignment.id)
            .options(joinedload(ReminderUser.user))
        )
        .unique()
        .scalar_one()
    )
    return refreshed


def list_reminder_assignments(db: Session, reminder_id: uuid.UUID) -> list[ReminderUser]:
    stmt = (
        select(ReminderUser)
        .where(ReminderUser.reminder_id == reminder_id)
        .options(joinedload(ReminderUser.user))
        .order_by(ReminderUser.created_at.asc())
    )
    return list(db.execute(stmt).unique().scalars().all())


def remove_user_assignment(db: Session, reminder_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    assignment = db.execute(
        select(ReminderUser).where(ReminderUser.reminder_id == reminder_id, ReminderUser.user_id == user_id)
    ).scalar_one_or_none()
    if assignment is None:
        return False

    db.delete(assignment)
    db.commit()
    return True
