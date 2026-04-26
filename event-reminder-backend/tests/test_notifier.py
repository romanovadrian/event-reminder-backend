from datetime import date

from app.config import settings
from app.models import EventType, Reminder, User
from app.services import notifier


class _DummyMessage:
    sid = "SM123"


class _DummyMessages:
    def __init__(self):
        self.created_with = None

    def create(self, **kwargs):
        self.created_with = kwargs
        return _DummyMessage()


class _DummyClient:
    def __init__(self, account_sid, auth_token):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.messages = _DummyMessages()


def test_notifier_log_mode(caplog):
    reminder = Reminder(title="A", event_type=EventType.custom, event_date=date(2026, 1, 1), remind_days_before=0)
    user = User(
        full_name="Receiver",
        email="receiver@example.com",
        phone_number="+37369111240",
        hashed_password="hashed",
        timezone="UTC",
    )
    caplog.set_level("INFO")

    original_provider = settings.sms_provider
    settings.sms_provider = "log"

    notifier.send_event_reminder(reminder, user)

    settings.sms_provider = original_provider

    assert "REMINDER:" in caplog.text


def test_notifier_twilio_uses_user_phone(monkeypatch):
    reminder = Reminder(title="B", event_type=EventType.birthday, event_date=date(2026, 2, 2), remind_days_before=0)
    user = User(
        full_name="Receiver",
        email="receiver2@example.com",
        phone_number="+37369111241",
        hashed_password="hashed",
        timezone="UTC",
    )

    captured = {}

    class _InspectableClient(_DummyClient):
        def __init__(self, account_sid, auth_token):
            super().__init__(account_sid, auth_token)
            captured["client"] = self

    monkeypatch.setattr("twilio.rest.Client", _InspectableClient)

    original_provider = settings.sms_provider
    original_sid = settings.twilio_account_sid
    original_token = settings.twilio_auth_token
    original_from = settings.twilio_from_number

    settings.sms_provider = "twilio"
    settings.twilio_account_sid = "AC_test"
    settings.twilio_auth_token = "token_test"
    settings.twilio_from_number = "+12025550123"

    notifier.send_event_reminder(reminder, user)

    settings.sms_provider = original_provider
    settings.twilio_account_sid = original_sid
    settings.twilio_auth_token = original_token
    settings.twilio_from_number = original_from

    message_kwargs = captured["client"].messages.created_with
    assert message_kwargs is not None
    assert message_kwargs["to"] == "+37369111241"
    assert message_kwargs["from_"] == "+12025550123"
