"""Multi-step conversations.

Some actions need the user to type more than one message (for example a habit
name or a reminder time). This file bundles all of those flows into one
ConversationHandler. Each flow is a small state machine:

    * ADD_HABIT   — /addhabit        -> bot asks for a name -> user types it
    * EDIT_HABIT  — tap 'Rename'     -> bot asks for a new name -> user types it
    * SET_TIME    — tap 'Set time'   -> bot asks for HH:MM -> user types it
    * MOOD_WAIT   — /mood            -> bot shows 1-10 buttons -> user taps one
    * MOOD_NOTE   — after the tap    -> bot asks for an optional note

The ConversationHandler works out the current state for each user and routes
their next message to the right place.
"""

import re

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database
import keyboards
import utils

# The different steps (states) of the conversations.
ADD_HABIT, EDIT_HABIT, SET_TIME, MOOD_WAIT, MOOD_NOTE = range(5)


# ---------------------------------------------------------------------------
# Adding a habit
# ---------------------------------------------------------------------------

async def start_add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point (via /addhabit or the 'Add a habit' button).

    Works both as '/addhabit Gym' and as plain '/addhabit' (the bot then asks
    for the name in the next message).
    """
    args = context.args
    if args:
        return await _save_habit_name(update, context, " ".join(args).strip())

    text = (
        "What would you like to call this habit? ✨\n\n"
        "Something small and specific works best, like *Gym*, "
        "*Read 20 pages* or *No sugar*."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboards.cancel_button()
        )
    else:
        await update.message.reply_text(text, reply_markup=keyboards.cancel_button())
    return ADD_HABIT


async def _save_habit_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE, name: str
) -> int:
    """Shared helper: validate and store a habit name, then show the list."""
    if len(name) > 40:
        await update.effective_chat.send_message(
            "That name is a bit long (max 40 characters). Try something shorter? 😊",
            reply_markup=keyboards.cancel_button(),
        )
        return ADD_HABIT

    database.add_habit(update.effective_user.id, name)

    await update.effective_chat.send_message(
        f"Added *{name}* to your habits! 🎉\n\n"
        "You can mark it done today with the buttons in /habits, "
        "or just type `/done {name}`."
    )
    await _show_habits_after(update, context)
    return ConversationHandler.END


async def save_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The user typed a habit name — save it."""
    return await _save_habit_name(update, context, update.message.text.strip())


# ---------------------------------------------------------------------------
# Renaming a habit
# ---------------------------------------------------------------------------

async def start_edit_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point (tap the ✏️ Rename button on a habit)."""
    query = update.callback_query
    await query.answer()

    habit_id = int(query.data.split(":")[1])
    habit = database.get_habit_by_id(habit_id, query.from_user.id)
    if not habit:
        await query.edit_message_text("Hmm, that habit no longer exists. 🤔")
        return ConversationHandler.END

    context.user_data["edit_habit_id"] = habit_id
    await query.edit_message_text(
        f"What should *{habit['name']}* be called instead?",
        reply_markup=keyboards.cancel_button(),
    )
    return EDIT_HABIT


async def save_edit_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The user typed the new name."""
    new_name = update.message.text.strip()
    if len(new_name) > 40:
        await update.message.reply_text(
            "That name is a bit long (max 40 characters). Try something shorter? 😊",
            reply_markup=keyboards.cancel_button(),
        )
        return EDIT_HABIT

    habit_id = context.user_data.pop("edit_habit_id", None)
    if habit_id:
        database.rename_habit(habit_id, update.effective_user.id, new_name)
        await update.message.reply_text(f"Renamed it to *{new_name}*! ✏️")
    await _show_habits_after(update, context)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Setting the reminder time
# ---------------------------------------------------------------------------

async def start_set_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point (tap the 'Set reminder time' button)."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "What time should your evening check-in arrive? ⏰\n\n"
        "Type it in 24-hour format, e.g. *20:00* or *09:30*.",
        reply_markup=keyboards.cancel_button(),
    )
    return SET_TIME


async def save_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The user typed a time — validate and save it."""
    text = update.message.text.strip()
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", text)
    if not match:
        await update.message.reply_text(
            "That doesn't look like a valid time. Please use 24-hour format, "
            "like *20:00* or *09:30*. 😊",
            reply_markup=keyboards.cancel_button(),
        )
        return SET_TIME

    hhmm = f"{int(match.group(1)):02d}:{match.group(2)}"
    database.set_reminder_time(update.effective_user.id, hhmm)

    await update.message.reply_text(
        f"Perfect! I'll check in with you every day at *{hhmm}* 💛\n\n"
        "If that time stops working for you, you can change it anytime in "
        "/reminders."
    )
    await _show_reminders_after(update, context)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Mood check-in
# ---------------------------------------------------------------------------

async def start_mood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point (via /mood or the 'Log my mood' button)."""
    user_id = update.effective_user.id
    offset = database.get_timezone_offset(user_id)
    today = utils.local_today(offset)
    existing = database.get_mood(user_id, today)

    if existing:
        text = (
            f"You already logged *{existing['mood']}/10* "
            f"{utils.mood_emoji(existing['mood'])} today.\n\n"
            "Feeling different now? Pick a number to update it, "
            "or just tap Cancel."
        )
    else:
        text = (
            "How are you feeling today? 😊\n\n"
            "Pick a number from 1 (really low) to 10 (fantastic)."
        )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboards.mood_keyboard_markup()
        )
    else:
        await update.message.reply_text(text, reply_markup=keyboards.mood_keyboard_markup())
    return MOOD_WAIT


async def mood_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The user tapped a number 1-10. Ask for an optional note."""
    query = update.callback_query
    await query.answer()

    mood = int(query.data.split(":")[1])
    context.user_data["pending_mood"] = mood

    await query.edit_message_text(
        f"Got it — *{mood}/10* {utils.mood_emoji(mood)}.\n\n"
        "Want to add a short note about why? (Optional — just type it, "
        "or skip.)",
        reply_markup=keyboards.mood_note_markup(),
    )
    return MOOD_NOTE


async def save_mood_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The user typed a note for today's mood."""
    mood = context.user_data.pop("pending_mood", 0)
    note = update.message.text.strip()[:280]
    user_id = update.effective_user.id
    today = utils.local_today(database.get_timezone_offset(user_id))
    database.add_or_update_mood(user_id, today, mood, note)

    await update.message.reply_text(
        f"Logged *{mood}/10* {utils.mood_emoji(mood)} with a note. 💛\n\n"
        f"Thanks for checking in — that *{utils.mood_word(mood)}* feeling "
        "is totally valid. See you tomorrow!"
    )
    return ConversationHandler.END


async def skip_mood_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The user pressed 'Skip the note'."""
    query = update.callback_query
    await query.answer()

    mood = context.user_data.pop("pending_mood", 0)
    user_id = query.from_user.id
    today = utils.local_today(database.get_timezone_offset(user_id))
    database.add_or_update_mood(user_id, today, mood, None)

    await query.edit_message_text(
        f"Logged *{mood}/10* {utils.mood_emoji(mood)}. 💛\n\n"
        "Thanks for checking in. Whatever you're feeling is valid — "
        "see you tomorrow!"
    )
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Cancelling and helpers
# ---------------------------------------------------------------------------

async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current flow (via /cancel or the Cancel button)."""
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Okay, no problem. 😊")
    else:
        await update.message.reply_text("Okay, no problem. 😊")
    return ConversationHandler.END


async def unmatched_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """If a user types something unexpected mid-flow, give a gentle nudge."""
    await update.message.reply_text(
        "That doesn't quite fit what we're doing right now. 😊\n\n"
        "You can send /cancel to stop, or just answer the question above."
    )


async def _show_habits_after(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """After adding/renaming a habit, show the refreshed habit list."""
    from handlers import messages  # local import to keep things simple
    text, markup = messages.build_habits_view(update.effective_user.id)
    await update.effective_chat.send_message(text, reply_markup=markup)


async def _show_reminders_after(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """After setting a time, show the reminders screen."""
    from handlers import messages  # local import to keep things simple
    text, markup = messages.build_reminders_view(update.effective_user.id)
    await update.effective_chat.send_message(text, reply_markup=markup)


# ---------------------------------------------------------------------------
# The single conversation handler that ties all the flows together
# ---------------------------------------------------------------------------

main_conversation = ConversationHandler(
    # Ways a conversation can start.
    entry_points=[
        CommandHandler("addhabit", start_add_habit),
        CallbackQueryHandler(start_add_habit, pattern="^addhabit$"),
        CallbackQueryHandler(start_edit_habit, pattern="^he:\\d+$"),
        CallbackQueryHandler(start_set_time, pattern="^settime$"),
        CommandHandler("mood", start_mood),
        CallbackQueryHandler(start_mood, pattern="^mood$"),
    ],
    # What to do in each state.
    states={
        ADD_HABIT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_habit),
        ],
        EDIT_HABIT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_edit_habit),
        ],
        SET_TIME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_time),
        ],
        MOOD_WAIT: [
            CallbackQueryHandler(mood_selected, pattern="^mood:\\d+$"),
        ],
        MOOD_NOTE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_mood_note),
            CallbackQueryHandler(skip_mood_note, pattern="^mood_note_skip$"),
        ],
    },
    # Ways to leave a conversation early.
    fallbacks=[
        CommandHandler("cancel", cancel_flow),
        CallbackQueryHandler(cancel_flow, pattern="^cancel_flow$"),
        # NOTE: '~filters.COMMAND' is important — otherwise slash-commands
        # would get swallowed here while a flow is active.
        MessageHandler(filters.TEXT & ~filters.COMMAND, unmatched_text),
    ],
)