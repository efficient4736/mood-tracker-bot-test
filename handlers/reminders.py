"""The daily reminder job.

A background task runs every minute. For each user with reminders on, it checks
their local time (based on their time zone). When it reaches their reminder
time — and the reminder hasn't been sent that day yet — it sends a friendly
evening check-in.

Checking every minute is simple and reliable: no complicated scheduling,
and it always matches the user's stored reminder time exactly.
"""

import logging
from datetime import datetime, timedelta, timezone

from telegram.ext import ContextTypes

import database
import utils
from handlers import messages

logger = logging.getLogger(__name__)


async def _send_checkin(context: ContextTypes.DEFAULT_TYPE, user: dict) -> None:
    """Send one user their evening check-in message."""
    text, markup = messages.build_checkin(user["id"])
    await context.bot.send_message(chat_id=user["id"], text=text, reply_markup=markup)
    logger.info("Sent evening check-in to user %s", user["id"])


async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called every 60 seconds by the job queue. Sends due reminders."""
    try:
        users = database.get_all_users()
        now_utc = datetime.now(timezone.utc)

        for user in users:
            # Only users who have enabled reminders and set a time.
            if not user["reminders_enabled"] or not user["reminder_time"]:
                continue

            # Their local time right now.
            local_now = now_utc + timedelta(hours=user["timezone_offset"] or 0)
            today = local_now.date().isoformat()

            # Don't send twice on the same day.
            if user["last_reminder_date"] == today:
                continue

            # Has the reminder time been reached in their time zone?
            if local_now.strftime("%H:%M") < user["reminder_time"]:
                continue

            # Send the check-in and remember we did.
            try:
                await _send_checkin(context, user)
                database.set_last_reminder_date(user["id"], today)
            except Exception:
                # One user failing must not break the loop for the others.
                logger.exception("Could not send reminder to user %s", user["id"])
    except Exception:
        logger.exception("Reminder job crashed")