"""Callback-button router.

Buttons send a small piece of 'callback data' (e.g. 'hd:3' = mark habit 3 done).
This file decides what each piece of data means and reacts. The conversation
system in flows.py handles its own buttons first; everything else lands here.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

import database
import keyboards
import utils
from handlers import messages

logger = logging.getLogger(__name__)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """The main router for every button press."""
    query = update.callback_query
    await query.answer()  # acknowledge the press (stops the loading spinner)
    data = query.data
    user_id = query.from_user.id

    # --- Buttons owned by the conversation system (ignore them here) ------
    if data in ("mood", "addhabit", "settime", "cancel_flow") or data.startswith(
        ("mood:", "he:")
    ):
        return

    # --- Main menu ---------------------------------------------------------
    if data == "menu":
        await query.edit_message_text(
            messages.main_menu_text(), reply_markup=keyboards.main_menu_markup()
        )
        return

    if data == "help":
        await query.edit_message_text(
            messages.help_text(), reply_markup=keyboards.main_menu_markup()
        )
        return

    if data == "habits":
        text, markup = messages.build_habits_view(user_id)
        await query.edit_message_text(text, reply_markup=markup)
        return

    if data == "stats":
        await query.edit_message_text(
            messages.build_stats_text(user_id),
            reply_markup=keyboards.main_menu_markup(),
        )
        return

    if data in ("reminders", "settings"):
        text, markup = messages.build_reminders_view(user_id)
        await query.edit_message_text(text, reply_markup=markup)
        return

    # --- Mark a habit done / undo ------------------------------------------
    if data.startswith("hd:"):
        await _mark_done(query, user_id)
        return

    if data.startswith("hu:"):
        await _undo_done(query, user_id)
        return

    # --- Delete a habit (with confirmation) --------------------------------
    if data.startswith("hdel:"):
        habit_id = int(data.split(":")[1])
        habit = database.get_habit_by_id(habit_id, user_id)
        if habit:
            await query.edit_message_text(
                f"Delete *{habit['name']}* and its whole history? 🗑️",
                reply_markup=keyboards.confirm_delete_markup(habit_id, habit["name"]),
            )
        return

    if data.startswith("hdelc:"):
        habit_id = int(data.split(":")[1])
        habit = database.get_habit_by_id(habit_id, user_id)
        if habit:
            database.delete_habit(habit_id, user_id)
            await query.edit_message_text(
                f"Deleted *{habit['name']}*. 💨\n\nNo hard feelings — "
                "you can always start it again later."
            )
        text, markup = messages.build_habits_view(user_id)
        await query.message.reply_text(text, reply_markup=markup)
        return

    if data == "hdelx":
        text, markup = messages.build_habits_view(user_id)
        await query.edit_message_text(text, reply_markup=markup)
        return

    # --- Time zone -----------------------------------------------------------
    if data == "settz":
        await query.edit_message_text(
            "Which time zone are you in? 🌍\n\n"
            "Pick the UTC offset closest to you, or send me a text like "
            "*UTC+2*, *+2* or *-5.5* and I'll use that.",
            reply_markup=keyboards.timezone_markup(),
        )
        return

    if data.startswith("tz:"):
        try:
            offset = float(data.split(":")[1])
        except ValueError:
            return
        database.set_timezone(user_id, offset)
        text, markup = messages.build_reminders_view(user_id)
        await query.edit_message_text(
            f"Saved your time zone as {utils.format_offset(offset)}. ✅\n\n{text}",
            reply_markup=markup,
        )
        return

    # --- Pause / resume reminders -------------------------------------------
    if data == "remtoggle":
        user = database.get_user(user_id)
        currently_on = bool(user["reminders_enabled"]) if user else False
        database.set_reminders_enabled(user_id, not currently_on)
        word = "Resumed" if not currently_on else "Paused"
        text, markup = messages.build_reminders_view(user_id)
        await query.edit_message_text(
            f"{word} reminders. ✅\n\n{text}", reply_markup=markup
        )
        return

    # --- A button we do not recognise ----------------------------------------
    logger.info("Unhandled callback data: %s", data)
    await query.edit_message_text(
        messages.main_menu_text(), reply_markup=keyboards.main_menu_markup()
    )


async def _mark_done(query, user_id: int) -> None:
    """Mark a habit done for today and refresh the list."""
    habit_id = int(query.data.split(":")[1])
    habit = database.get_habit_by_id(habit_id, user_id)
    if not habit:
        return

    today = utils.local_today(database.get_timezone_offset(user_id))
    inserted = database.mark_done(habit["id"], user_id, today)

    if inserted:
        streak = database.current_streak(habit["id"], today)
        await query.edit_message_text(
            f"*{habit['name']}* done! ✅\n\n{utils.streak_message(habit['name'], streak)}"
        )
    else:
        await query.edit_message_text(
            f"*{habit['name']}* was already done today — even better! 💛"
        )

    # Refresh the habit list underneath.
    text, markup = messages.build_habits_view(user_id)
    await query.message.reply_text(text, reply_markup=markup)


async def _undo_done(query, user_id: int) -> None:
    """Undo today's 'done' mark and refresh the list."""
    habit_id = int(query.data.split(":")[1])
    habit = database.get_habit_by_id(habit_id, user_id)
    if not habit:
        return

    today = utils.local_today(database.get_timezone_offset(user_id))
    database.undo_done(habit["id"], user_id, today)
    await query.edit_message_text(
        f"Okay, I've un-marked *{habit['name']}*. ↩️\n\nNo worries — "
        "the day isn't over yet."
    )

    text, markup = messages.build_habits_view(user_id)
    await query.message.reply_text(text, reply_markup=markup)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called automatically whenever any handler raises an exception."""
    logger.exception("An error happened while handling an update")

    # Try to tell the user something went wrong (if we know who they are).
    try:
        if isinstance(update, Update) and update.effective_user:
            await update.effective_user.send_message(
                "Oops — something went wrong on my end. 😅 "
                "It's not your fault; please try again in a moment."
            )
    except Exception:  # if even the apology fails, just log it
        logger.exception("Could not send the error message to the user")