import logging

from app.config import settings
from app.models import Reminder, User

logger = logging.getLogger("event-reminder")


def send_event_reminder(reminder: Reminder, user: User) -> None:
    if settings.sms_provider == "twilio":
        _send_with_twilio(reminder, user)
        return

    logger.info(
        "REMINDER: %s to %s (%s) in timezone %s",
        reminder.title,
        user.phone_number,
        reminder.event_type.value,
        user.timezone,
    )


def _send_with_twilio(reminder: Reminder, user: User) -> None:
    required = [
        settings.twilio_account_sid,
        settings.twilio_auth_token,
        settings.twilio_from_number,
    ]
    if not all(required):
        logger.warning(
            "SMS provider is set to twilio, but required Twilio env vars are missing. "
            "Falling back to log output."
        )
        logger.info("REMINDER: %s to %s", reminder.title, user.phone_number)
        return

    # Import locally so the app can still run without Twilio installed when provider is not used.
    from twilio.rest import Client

    body = (
        f"Reminder: {reminder.title} "
        f"({reminder.event_type.value}) on {reminder.event_date.isoformat()}."
    )

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    message = client.messages.create(
        body=body,
        from_=settings.twilio_from_number,
        to=user.phone_number,
    )

    logger.info("Twilio SMS sent with sid=%s", message.sid)
