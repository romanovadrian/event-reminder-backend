from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import SessionLocal
from app.models import Reminder, ReminderUser
from app.services.notifier import send_event_reminder

logger = logging.getLogger("event-reminder")


class ReminderScheduler:
    def run_once(self) -> None:
        with SessionLocal() as db:
            stmt = (
                select(Reminder)
                .where(Reminder.is_active.is_(True))
                .options(joinedload(Reminder.user_links).joinedload(ReminderUser.user))
            )
            reminders = list(db.execute(stmt).unique().scalars().all())

            for reminder in reminders:
                for assignment in reminder.user_links:
                    if not assignment.user.is_active:
                        continue

                    if self._should_trigger(reminder, assignment):
                        self._trigger(reminder, assignment)
                        assignment.last_notified_on = datetime.now(ZoneInfo(assignment.user.timezone)).date()
                        db.add(assignment)

            db.commit()

    def _should_trigger(self, reminder: Reminder, assignment: ReminderUser) -> bool:
        local_now = datetime.now(ZoneInfo(assignment.user.timezone))
        occurrence = self._next_occurrence(reminder.event_date, local_now.date())
        reminder_date = occurrence - timedelta(days=reminder.remind_days_before)

        if local_now.date() != reminder_date:
            return False

        if assignment.last_notified_on == local_now.date():
            return False

        trigger_time = local_now.replace(
            hour=assignment.notify_time.hour,
            minute=assignment.notify_time.minute,
            second=0,
            microsecond=0,
        )
        return local_now >= trigger_time

    @staticmethod
    def _next_occurrence(original_date: date, current_date: date) -> date:
        this_year = ReminderScheduler._safe_date(current_date.year, original_date.month, original_date.day)
        if this_year >= current_date:
            return this_year
        return ReminderScheduler._safe_date(current_date.year + 1, original_date.month, original_date.day)

    @staticmethod
    def _safe_date(year: int, month: int, day: int) -> date:
        # Preserve reminders for leap-day events by falling back to Feb 28 on non-leap years.
        if month == 2 and day == 29:
            try:
                return date(year, month, day)
            except ValueError:
                return date(year, 2, 28)
        return date(year, month, day)

    @staticmethod
    def _trigger(reminder: Reminder, assignment: ReminderUser) -> None:
        send_event_reminder(reminder, assignment.user)


scheduler = ReminderScheduler()


def get_poll_interval() -> int:
    return settings.poll_interval_seconds
