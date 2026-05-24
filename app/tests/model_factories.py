import datetime
from typing import Any, Generic, TypeVar

from app.models import Reminder, ReminderUser, User

T = TypeVar("T")


class BaseFactory(Generic[T]):
    obj_cls: type[T]

    def dump(self) -> dict[str, Any]:
        return vars(self)

    def post_data(self) -> dict[str, Any]:
        raise NotImplementedError

    def return_object(self) -> T:
        return self.obj_cls(**self.post_data())
    
class UserFactory(BaseFactory[User]):
    obj_cls = User

    def __generate_unique_phone_number(self) -> str:
        # Generate a unique phone number based on the current timestamp
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        return f"+373{timestamp % 10000000000:010d}"

    def __init__(self, email: str = "user@example.com", password: str = "password123", full_name: str = "Test User", phone_number: str = None, timezone: str = "UTC"):
        if phone_number is None:
            phone_number = self.__generate_unique_phone_number()
        self.email = email
        self.password = password
        self.full_name = full_name
        self.phone_number = phone_number
        self.timezone = timezone

    def post_data(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "hashed_password": self.password,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "timezone": self.timezone,
        }

class ReminderFactory(BaseFactory[Reminder]):
    obj_cls = Reminder

    def __init__(self, title: str, event_date: datetime.date, event_type: str = "custom", remind_days_before: int = 0, notes: str | None = None):
        self.title = title
        self.event_date = event_date
        self.event_type = event_type
        self.remind_days_before = remind_days_before
        self.notes = notes

    def post_data(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "event_date": self.event_date,
            "event_type": self.event_type,
            "remind_days_before": self.remind_days_before,
            "notes": self.notes,
        }
    
class ReminderUserFactory(BaseFactory[ReminderUser]):
    obj_cls = ReminderUser

    def __init__(self, reminder_id: str, user_id: str, notify_time: datetime.time = datetime.time(0, 0, 0)):
        self.reminder_id = reminder_id
        self.user_id = user_id
        self.notify_time = notify_time

    def post_data(self) -> dict[str, Any]:
        return {
            "reminder_id": self.reminder_id,
            "user_id": self.user_id,
            "notify_time": self.notify_time,
        }