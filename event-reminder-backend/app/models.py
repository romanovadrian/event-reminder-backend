import enum
import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class EventType(str, enum.Enum):
    birthday = "birthday"
    anniversary = "anniversary"
    custom = "custom"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String(24), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    reminder_links: Mapped[list["ReminderUser"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType, name="event_type"), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    remind_days_before: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user_links: Mapped[list["ReminderUser"]] = relationship(back_populates="reminder", cascade="all, delete-orphan")


class ReminderUser(Base):
    __tablename__ = "reminder_users"
    __table_args__ = (UniqueConstraint("reminder_id", "user_id", name="uq_reminder_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reminder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reminders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notify_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(hour=9, minute=0))
    last_notified_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    reminder: Mapped[Reminder] = relationship(back_populates="user_links")
    user: Mapped[User] = relationship(back_populates="reminder_links")
