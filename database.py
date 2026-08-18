"""All database access for the bot.

We use SQLite, which is a small database that lives in a single file on your
machine (data/moodbot.db). No server to install, no configuration - perfect for
a personal bot.

Every function here is a small, self-contained helper. The rest of the program
never talks to SQLite directly; it only calls these functions.

Tables:
    users        -> one row per person who uses the bot
    habits       -> the habits a user wants to track
    habit_logs   -> one row per habit per day ("done" records)
    mood_logs    -> one row per user per day (a mood check-in)
"""

import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta

import config

# ---------------------------------------------------------------------------
# Database schema (created automatically the first time you run the bot)
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id                  INTEGER PRIMARY KEY,          -- the Telegram user id
    username            TEXT,                          -- their @username
    first_name          TEXT,                          -- their first name
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    reminder_time       TEXT,                          -- e.g. '20:00' (None = not set)
    reminders_enabled   INTEGER NOT NULL DEFAULT 0,    -- 1 = reminders on, 0 = off
    timezone_offset     REAL NOT NULL DEFAULT 0,       -- hours from UTC, e.g. 1 or -5.5
    last_reminder_date  TEXT                           -- last day a reminder was sent
);

CREATE TABLE IF NOT EXISTS habits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS habit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id    INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,                         -- 'YYYY-MM-DD'
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(habit_id, date)                             -- a habit can only be done once/day
);

CREATE TABLE IF NOT EXISTS mood_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,                         -- 'YYYY-MM-DD'
    mood        INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 10),
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, date)                              -- one mood check-in per day
);
"""


@contextmanager
def _connect():
    """Open a connection to the database (used internally by all functions).

    The "with ... as conn:" block makes sure the connection is always closed
    and every change is saved (committed), even if an error happens.
    """
    conn = sqlite3.connect(config.DATABASE_PATH, timeout=15)
    conn.row_factory = sqlite3.Row  # rows behave like dictionaries: row["name"]
    conn.execute("PRAGMA journal_mode = WAL;").fetchall()  # faster + safer writes
    conn.execute("PRAGMA foreign_keys = ON;").fetchall()   # keep data tidy
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create the tables if they do not exist yet. Run once at startup."""
    with _connect() as conn:
        conn.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def upsert_user(user_id: int, username: str | None, first_name: str | None) -> None:
    """Save (or update) a user. Safe to call every time they write to the bot."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username    = excluded.username,
                first_name  = excluded.first_name
            """,
            (user_id, username, first_name),
        )


def get_user(user_id: int) -> dict | None:
    """Return one user as a dictionary, or None if they do not exist."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_all_users() -> list[dict]:
    """Return every user. Used by the reminder job each minute."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM users").fetchall()
        return [dict(r) for r in rows]


def get_timezone_offset(user_id: int) -> float:
    """Hours from UTC for a user (0 if unknown). Used to figure out 'today'."""
    user = get_user(user_id)
    return float(user["timezone_offset"]) if user else 0.0


def set_reminder_time(user_id: int, hhmm: str) -> None:
    """Store the reminder time ('HH:MM') and turn reminders on."""
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET reminder_time = ?, reminders_enabled = 1, "
            "last_reminder_date = NULL WHERE id = ?",
            (hhmm, user_id),
        )


def set_reminders_enabled(user_id: int, enabled: bool) -> None:
    """Turn reminders on (True) or off (False)."""
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET reminders_enabled = ? WHERE id = ?",
            (1 if enabled else 0, user_id),
        )


def set_timezone(user_id: int, offset: float) -> None:
    """Save the user's UTC offset (e.g. 1 for UTC+1, -5.5 for UTC-5:30)."""
    with _connect() as conn:
        conn.execute("UPDATE users SET timezone_offset = ? WHERE id = ?", (offset, user_id))


def set_last_reminder_date(user_id: int, day: str) -> None:
    """Remember which day the reminder was last sent on (so we send once/day)."""
    with _connect() as conn:
        conn.execute("UPDATE users SET last_reminder_date = ? WHERE id = ?", (day, user_id))


# ---------------------------------------------------------------------------
# Habits
# ---------------------------------------------------------------------------

def add_habit(user_id: int, name: str) -> int:
    """Create a new habit and return its id."""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO habits (user_id, name) VALUES (?, ?)", (user_id, name)
        )
        return int(cur.lastrowid)


def get_habits(user_id: int) -> list[dict]:
    """All habits for a user, oldest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM habits WHERE user_id = ? ORDER BY created_at, id", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_habit_by_id(habit_id: int, user_id: int) -> dict | None:
    """One habit, but only if it belongs to this user (safety check)."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def find_habit_by_name(user_id: int, name: str) -> dict | None:
    """Find a habit by name (case-insensitive), used by the /done command."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM habits WHERE user_id = ? AND lower(name) = lower(?) "
            "ORDER BY created_at LIMIT 1",
            (user_id, name),
        ).fetchone()
        return dict(row) if row else None


def rename_habit(habit_id: int, user_id: int, new_name: str) -> None:
    """Give a habit a new name."""
    with _connect() as conn:
        conn.execute(
            "UPDATE habits SET name = ? WHERE id = ? AND user_id = ?",
            (new_name, habit_id, user_id),
        )


def delete_habit(habit_id: int, user_id: int) -> None:
    """Delete a habit and all of its history."""
    with _connect() as conn:
        conn.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))


def count_habits(user_id: int) -> int:
    """How many habits a user has."""
    with _connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM habits WHERE user_id = ?", (user_id,)
        ).fetchone()[0]


# ---------------------------------------------------------------------------
# Habit logs (the "done" records)
# ---------------------------------------------------------------------------

def mark_done(habit_id: int, user_id: int, day: str) -> bool:
    """Mark a habit as done on a given day. Returns True if it was newly marked.

    If it was already marked done, nothing changes and we return False.
    """
    with _connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO habit_logs (habit_id, date) VALUES (?, ?)",
            (habit_id, day),
        )
        return cur.rowcount > 0


def undo_done(habit_id: int, user_id: int, day: str) -> None:
    """Remove the 'done' mark for a habit on a given day."""
    with _connect() as conn:
        conn.execute(
            "DELETE FROM habit_logs WHERE habit_id = ? AND date = ?", (habit_id, day)
        )


def is_done(habit_id: int, day: str) -> bool:
    """Was a habit marked done on a given day?"""
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM habit_logs WHERE habit_id = ? AND date = ?",
            (habit_id, day),
        ).fetchone()
        return row is not None


def _done_dates(habit_id: int) -> set[str]:
    """All dates a habit was done on, as a set of 'YYYY-MM-DD' strings."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT date FROM habit_logs WHERE habit_id = ?", (habit_id,)
        ).fetchall()
        return {r["date"] for r in rows}


def current_streak(habit_id: int, today: str) -> int:
    """The current streak in days.

    A streak counts consecutive days ending today (if done today) or ending
    yesterday (the streak is still alive, you just have not done it yet today).
    """
    dates = _done_dates(habit_id)
    day = date.fromisoformat(today)
    if today not in dates:
        day -= timedelta(days=1)
    streak = 0
    while day.isoformat() in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def longest_streak(habit_id: int) -> int:
    """The longest streak this habit has ever reached."""
    dates = sorted(_done_dates(habit_id))
    best = current = 0
    previous: date | None = None
    for day_str in dates:
        day = date.fromisoformat(day_str)
        if previous and (day - previous).days == 1:
            current += 1
        else:
            current = 1
        best = max(best, current)
        previous = day
    return best


def days_done_in_range(habit_id: int, start: str, end: str) -> int:
    """How many days a habit was done between start and end (inclusive)."""
    with _connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM habit_logs "
            "WHERE habit_id = ? AND date BETWEEN ? AND ?",
            (habit_id, start, end),
        ).fetchone()[0]


# ---------------------------------------------------------------------------
# Mood logs
# ---------------------------------------------------------------------------

def add_or_update_mood(user_id: int, day: str, mood: int, note: str | None) -> None:
    """Save a mood check-in. If one exists for the same day it is replaced."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO mood_logs (user_id, date, mood, note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                mood = excluded.mood,
                note = excluded.note
            """,
            (user_id, day, mood, note),
        )


def get_mood(user_id: int, day: str) -> dict | None:
    """The mood check-in for a user on a given day, or None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM mood_logs WHERE user_id = ? AND date = ?",
            (user_id, day),
        ).fetchone()
        return dict(row) if row else None


def get_moods_in_range(user_id: int, start: str, end: str) -> list[dict]:
    """All mood check-ins between start and end (inclusive), oldest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM mood_logs WHERE user_id = ? AND date BETWEEN ? AND ? "
            "ORDER BY date",
            (user_id, start, end),
        ).fetchall()
        return [dict(r) for r in rows]
