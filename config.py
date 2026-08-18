"""Configuration for the bot.

Everything that depends on your local machine or on secret values lives here.
The only thing you MUST configure is the Telegram bot token (in your .env file).

This file:
  * Loads values from the .env file (if it exists).
  * Reads the BOT_TOKEN from the environment.
  * Decides where the SQLite database file should live.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths (where files live on disk)
# ---------------------------------------------------------------------------

# The folder that contains this file = the project root folder.
BASE_DIR = Path(__file__).resolve().parent

# The .env file sits next to config.py.
ENV_FILE = BASE_DIR / ".env"

# All data (the SQLite database) is stored in a "data" folder.
DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "moodbot.db"

# ---------------------------------------------------------------------------
# Settings that get filled in from the environment
# ---------------------------------------------------------------------------

BOT_TOKEN = ""      # Your Telegram bot token (from BotFather).
LOG_LEVEL = "INFO"  # How much logging output you want: DEBUG, INFO, WARNING, ERROR


def load_config() -> None:
    """Read the .env file and the environment variables into the settings above.

    Call this once, at the very start of the program (in main.py).
    """
    global BOT_TOKEN, LOG_LEVEL

    # If a .env file exists next to config.py, load values from it.
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)

    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # A token is essential: without it the bot cannot talk to Telegram.
    if not BOT_TOKEN:
        raise SystemExit(
            "No BOT_TOKEN found. Please create a .env file "
            "(copy .env.example and fill in your token) - see the README."
        )

    # Make sure the folder that will hold the database exists.
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
