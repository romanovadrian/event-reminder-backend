import uuid
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import EventType


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    phone_number: str = Field(min_length=8, max_length=24)
    password: str = Field(min_length=8, max_length=128)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    is_active: bool = True

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not value.startswith("+"):
            raise ValueError("phone_number must be in E.164 format, for example +373XXXXXXXX")
        digits = value[1:]
        if not digits.isdigit():
            raise ValueError("phone_number must contain digits after '+'")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception as exc:
            raise ValueError("Invalid IANA timezone") from exc
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    phone_number: str
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserAdminCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    phone_number: str = Field(min_length=8, max_length=24)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    is_active: bool = True

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not value.startswith("+"):
            raise ValueError("phone_number must be in E.164 format, for example +373XXXXXXXX")
        digits = value[1:]
        if not digits.isdigit():
            raise ValueError("phone_number must contain digits after '+'")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception as exc:
            raise ValueError("Invalid IANA timezone") from exc
        return value


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    event_type: EventType
    event_date: date
    remind_days_before: int = Field(default=0, ge=0, le=365)
    notes: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    event_type: EventType | None = None
    event_date: date | None = None
    remind_days_before: int | None = Field(default=None, ge=0, le=365)
    notes: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    event_type: EventType
    event_date: date
    remind_days_before: int
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ReminderAssignmentCreate(BaseModel):
    user_id: uuid.UUID
    notify_time: time = Field(default=time(hour=9, minute=0))


class ReminderAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reminder_id: uuid.UUID
    user_id: uuid.UUID
    notify_time: time
    last_notified_on: date | None
    created_at: datetime
    user: UserRead
