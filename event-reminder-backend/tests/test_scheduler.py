from datetime import datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy.orm import sessionmaker

from app.models import EventType, Reminder, ReminderUser, User
from app.services import scheduler as scheduler_module


def test_scheduler_sends_once_per_user_per_day(db_session, monkeypatch):
    sent_to = []

    def fake_send_event_reminder(reminder, user):
        sent_to.append((str(reminder.id), user.phone_number))

    monkeypatch.setattr(scheduler_module, "send_event_reminder", fake_send_event_reminder)

    test_session_local = sessionmaker(bind=db_session.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr(scheduler_module, "SessionLocal", test_session_local)

    today = datetime.now(ZoneInfo("UTC")).date()

    user_1 = User(
        full_name="Receiver One",
        email="receiver1@example.com",
        phone_number="+37369111230",
        hashed_password="hashed",
        timezone="UTC",
    )
    user_2 = User(
        full_name="Receiver Two",
        email="receiver2@example.com",
        phone_number="+37369111231",
        hashed_password="hashed",
        timezone="UTC",
    )
    reminder = Reminder(
        title="Birthday Reminder",
        event_type=EventType.birthday,
        event_date=today,
        remind_days_before=0,
        is_active=True,
    )
    db_session.add_all([user_1, user_2, reminder])
    db_session.commit()

    link_1 = ReminderUser(reminder_id=reminder.id, user_id=user_1.id, notify_time=time(hour=0, minute=0))
    link_2 = ReminderUser(reminder_id=reminder.id, user_id=user_2.id, notify_time=time(hour=0, minute=0))
    db_session.add_all([link_1, link_2])
    db_session.commit()

    scheduler_module.scheduler.run_once()

    assert len(sent_to) == 2
    assert {entry[1] for entry in sent_to} == {"+37369111230", "+37369111231"}

    sent_to.clear()

    scheduler_module.scheduler.run_once()

    assert sent_to == []
