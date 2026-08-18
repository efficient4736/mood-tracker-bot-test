"""Slash-command handlers: /start, /help, /habits, /done, /stats, etc.

Each function here handles one command. They are short on purpose — anything
that builds a message or a keyboard lives in handlers/messages.py or keyboards.py.
"""

from telegram import Update
from telegram.ext import ContextTypes

import database
import keyboards
import utils
from handlers import messages


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — welcome the user, explain the bot, show the main menu."""
    user = update.effective_user
    database.upsert_user(user.id, user.username, user.first_name)

    db_user = database.get_user(user.id)
    name = db_user["first_name"] or "friend"

    text = (
        f"Hey {name}! 👋 Welcome to *Habit & Mood Companion*.\n\n"
        "I'm here to help you build habits and keep tabs on how you're "
        "feeling — with zero pressure and lots of encouragement. 💛\n\n"
        "Here's how it works:\n"
        "• Add a few habits with /addhabit\n"
        "• Tick them off each day with /done\n"
        "• Log a quick mood with /mood\n"
        "• Watch your streaks and stats grow with /stats\n\n"
        "Everything you share stays on *your* machine — no cloud, no snooping."
    )

    if not db_user["reminder_time"]:
        text += (
            "\n\nPS: you haven't set a reminder time yet. I can send you a "
            "gentle evening check-in — just tap *Reminders* below. 😊"
        )

    await update.message.reply_text(text, reply_markup=keyboards.main_menu_markup())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — list everything the bot can do."""
    await update.message.reply_text(
        messages.help_text(), reply_markup=keyboards.main_menu_markup()
    )


async def habits_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/habits — show all habits with their status and buttons."""
    text, markup = messages.build_habits_view(update.effective_user.id)
    await update.message.reply_text(text, reply_markup=markup)


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/done — mark a habit as done.

    With a name:    /done Gym
    Without a name: shows the habit list with Done buttons instead.
    """
    user_id = update.effective_user.id
    text = update.message.text
    parts = text.split(maxsplit=1)

    # No habit name given -> show the habit list with buttons.
    if len(parts) == 1:
        habit_text, markup = messages.build_habits_view(user_id)
        await update.message.reply_text(
            "Which habit did you finish? Tap the button below. 😊",
            reply_markup=markup,
        )
        return

    name = parts[1].strip()
    habit = database.find_habit_by_name(user_id, name)

    if not habit:
        names = [h["name"] for h in database.get_habits(user_id)]
        if names:
            await update.message.reply_text(
                f"I couldn't find a habit called *{name}*. Your habits are: "
                f"{', '.join(names)}.\n\nTry /done with one of those."
            )
        else:
            await update.message.reply_text(
                f"I couldn't find a habit called *{name}* — and you don't "
                "have any habits yet! Add one with /addhabit. ✨"
            )
        return

    today = utils.local_today(database.get_timezone_offset(user_id))
    inserted = database.mark_done(habit["id"], user_id, today)

    if inserted:
        streak = database.current_streak(habit["id"], today)
        await update.message.reply_text(
            f"*{habit['name']}* done for today! ✅\n\n{utils.streak_message(habit['name'], streak)}"
        )
    else:
        await update.message.reply_text(
            f"*{habit['name']}* is already marked done today — nice one! 💛"
        )

    # Show the updated list so they can keep going.
    habit_text, markup = messages.build_habits_view(user_id)
    await update.message.reply_text(habit_text, reply_markup=markup)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/stats — streaks, completion rates, mood average and trends."""
    text = messages.build_stats_text(update.effective_user.id)
    await update.message.reply_text(text, reply_markup=keyboards.main_menu_markup())


async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reminders — reminder time, pause/resume and time zone."""
    text, markup = messages.build_reminders_view(update.effective_user.id)
    await update.message.reply_text(text, reply_markup=markup)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/settings — same screen as /reminders (time zone etc.)."""
    text, markup = messages.build_reminders_view(update.effective_user.id)
    await update.message.reply_text(
        f"⚙️ *Settings*\n\n{text}", reply_markup=markup
    )


async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Any random text that isn't a command and isn't part of a flow."""
    await update.message.reply_text(
        "I didn't quite catch that. 😊 Try a command like /habits or /help, "
        "or tap a button below.",
        reply_markup=keyboards.main_menu_markup(),
    )