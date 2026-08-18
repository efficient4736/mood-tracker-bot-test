"""Habit & Mood Companion — main entry point.

Run this file to start the bot:        python main.py

It wires everything together:
    1. Loads configuration (token, paths).
    2. Creates the SQLite database if needed.
    3. Registers all commands, button handlers and conversations.
    4. Starts the reminder background job (checks every minute).
    5. Starts listening to Telegram (long polling) — this blocks forever.
"""

import logging
import warnings

# python-telegram-bot prints a harmless informational warning about the
# 'per_message' setting of ConversationHandler. It does not apply to our
# flows, so we silence just that one message to keep startup output clean.
warnings.filterwarnings(
    "ignore",
    message=r".*If 'per_message=False'.*",
)

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
import database
from handlers import callbacks, commands, reminders
from handlers.flows import main_conversation


def main() -> None:
    """Start the bot. Called only when this file is run directly."""
    # 1. Load settings from the .env file.
    config.load_config()

    # 2. Create the database tables if they don't exist yet.
    database.init_db()

    # 3. Set up logging so you can see what the bot is doing.
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Habit & Mood Companion...")

    # 4. Build the application (the brain of the bot).
    application = Application.builder().token(config.BOT_TOKEN).build()

    # 5. Register handlers. ORDER MATTERS: the conversation handler goes first
    #    so it can claim the buttons/messages that belong to active flows.
    application.add_handler(main_conversation)

    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("habits", commands.habits_command))
    application.add_handler(CommandHandler("done", commands.done_command))
    application.add_handler(CommandHandler("stats", commands.stats_command))
    application.add_handler(CommandHandler("reminders", commands.reminders_command))
    application.add_handler(CommandHandler("settings", commands.settings_command))

    # Any text that isn't a command and isn't part of a flow.
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, commands.fallback_text)
    )

    # All button presses that don't belong to a flow.
    application.add_handler(CallbackQueryHandler(callbacks.handle_callback))

    # Any error in any handler lands here (so the bot never crashes).
    application.add_error_handler(callbacks.error_handler)

    # 6. Start the reminder job: check once every 60 seconds.
    application.job_queue.run_repeating(
        reminders.check_reminders,
        interval=60,
        first=10,          # first check shortly after startup
        name="reminder_tick",
    )

    # 7. Listen for Telegram updates forever.
    #    drop_pending_updates=True means old messages from while the bot was
    #    offline are ignored instead of being replayed.
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()