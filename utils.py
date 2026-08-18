"""Small helper functions used across the bot: dates, timezones, celebrations.

Keeping these separate makes the rest of the code cleaner and easier to read.
"""

from datetime import date, datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Dates and timezones
#
# A user sets their timezone as an offset from UTC, e.g.:
#   UTC+1  -> offset 1     (Germany in winter)
#   UTC-5  -> offset -5    (New York)
#   UTC+5.5 -> offset 5.5  (India)
# We use that offset to decide what "today" and "now" mean for each user,
# because a day starts at different times in different parts of the world.
# ---------------------------------------------------------------------------

def local_datetime(offset_hours: float) -> datetime:
    """The current date and time in the user's timezone."""
    return datetime.now(timezone.utc) + timedelta(hours=offset_hours)


def local_today(offset_hours: float) -> str:
    """Today's date in the user's timezone, as 'YYYY-MM-DD'."""
    return local_datetime(offset_hours).date().isoformat()


def local_time_str(offset_hours: float) -> str:
    """The current local time as 'HH:MM'."""
    return local_datetime(offset_hours).strftime("%H:%M")


def add_days(day_str: str, delta: int) -> str:
    """A date string plus/minus some days, e.g. add_days('2026-08-18', -6)."""
    return (date.fromisoformat(day_str) + timedelta(days=delta)).isoformat()


def month_start(day_str: str) -> str:
    """The first day of the month a date belongs to."""
    return date.fromisoformat(day_str).replace(day=1).isoformat()


def weekday_short(day_str: str) -> str:
    """Short weekday name for a date, e.g. 'Mon'."""
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][
        date.fromisoformat(day_str).weekday()
    ]


def format_offset(offset: float) -> str:
    """Pretty label for a UTC offset, e.g. 1 -> 'UTC+1', 5.5 -> 'UTC+5.5'."""
    sign = "+" if offset >= 0 else "-"
    value = abs(offset)
    if value == int(value):
        return f"UTC{sign}{int(value)}"
    return f"UTC{sign}{value}"


def parse_offset(text: str) -> float | None:
    """Turn text like 'UTC+2', '+2', '-5.5' or '5.5' into a number.

    Returns None if the text does not look like a valid offset.
    """
    cleaned = text.strip().upper().replace("UTC", "").replace(" ", "")
    if cleaned in ("", "+", "-"):
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value < -12 or value > 14:  # realistic range of timezone offsets
        return None
    return value


# ---------------------------------------------------------------------------
# Mood helpers
# ---------------------------------------------------------------------------

MOOD_EMOJI = ["😞", "😔", "😕", "😐", "🙂", "😊", "😃", "🤩", "🥳", "🌟"]

MOOD_WORDS = [
    "tough", "rough", "meh", "okay", "decent",
    "good", "great", "really good", "amazing", "fantastic",
]


def mood_emoji(mood: int) -> str:
    """An emoji that matches a mood value from 1 to 10."""
    mood = max(1, min(10, int(mood)))
    return MOOD_EMOJI[mood - 1]


def mood_word(mood: int) -> str:
    """A friendly word that matches a mood value from 1 to 10."""
    mood = max(1, min(10, int(mood)))
    return MOOD_WORDS[mood - 1]


# ---------------------------------------------------------------------------
# Celebrations
# ---------------------------------------------------------------------------

# Streak lengths worth celebrating, and a warm message for each.
STREAK_MILESTONES = {
    3: "Three days in a row of {name}! 🎉 A habit is starting to form.",
    7: "One whole week of {name}! 🙌 That's a real habit now. So proud of you.",
    14: "Two weeks of {name} in a row! 💪 You're on fire.",
    21: "21 days of {name} - you've officially built the habit! 🏆",
    30: "30 days of {name}!! 🌟 That's a full month. Absolutely incredible.",
    60: "60 days of {name}! 🚀 You're unstoppable.",
    90: "90 days of {name}! 🎖️ Legendary consistency.",
    180: "Half a year of {name}! 👑 You're a machine.",
    365: "A FULL YEAR of {name}! 🏅 Words can't describe how amazing this is.",
}


def streak_message(name: str, streak: int) -> str:
    """A cheerful message for a streak. Uses the milestone text when relevant."""
    if streak in STREAK_MILESTONES:
        return STREAK_MILESTONES[streak].format(name=name)
    return f"Nice, {name} is on a {streak}-day streak! 🔥"


def mood_trend(previous_avg: float | None, recent_avg: float | None) -> str:
    """Describe whether mood is going up, down or staying the same."""
    if previous_avg is None or recent_avg is None:
        return "not enough data yet"
    if recent_avg - previous_avg >= 0.5:
        return "rising 📈"
    if previous_avg - recent_avg >= 0.5:
        return "dipping 📉"
    return "steady ➡️"


def mood_bar(mood: int) -> str:
    """A simple text bar chart for one mood value, e.g. '▓▓▓▓▓░░░░░'."""
    mood = max(1, min(10, int(mood)))
    return "▓" * mood + "░" * (10 - mood)
