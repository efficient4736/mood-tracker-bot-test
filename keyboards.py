"""Everything that builds Telegram inline keyboards (the buttons under messages).

Each function returns an InlineKeyboardMarkup ready to attach to a message.
Buttons communicate with the bot through a small 'callback_data' string,
for example 'hd:3' means "mark habit number 3 as done".
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# A tiny helper so the code below stays short and readable.
def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)


def main_menu_markup() -> InlineKeyboardMarkup:
    """The main menu: shown after /start and via the 'Home' button."""
    rows = [
        [_btn("📋 My habits", "habits"), _btn("✨ Add a habit", "addhabit")],
        [_btn("😊 Log my mood", "mood"), _btn("📊 My stats", "stats")],
        [_btn("⏰ Reminders", "reminders"), _btn("❓ Help", "help")],
    ]
    return InlineKeyboardMarkup(rows)


def home_button() -> InlineKeyboardMarkup:
    """A single 'back home' button, used at the bottom of long messages."""
    return InlineKeyboardMarkup([[_btn("🏠 Main menu", "menu")]])


def habit_action_markup(habit_id: int, done_today: bool) -> InlineKeyboardMarkup:
    """Buttons under one habit row: done, undo (if done), rename, delete."""
    buttons = [_btn("✅ Done", f"hd:{habit_id}")]
    if done_today:
        buttons.append(_btn("↩️ Undo", f"hu:{habit_id}"))
    buttons.append(_btn("✏️ Rename", f"he:{habit_id}"))
    buttons.append(_btn("🗑️ Delete", f"hdel:{habit_id}"))
    return InlineKeyboardMarkup([buttons])


def habits_footer_markup() -> InlineKeyboardMarkup:
    """Buttons below the habit list: add a habit and go home."""
    return InlineKeyboardMarkup([
        [_btn("✨ Add another habit", "addhabit")],
        [_btn("🏠 Main menu", "menu")],
    ])


def empty_habits_markup() -> InlineKeyboardMarkup:
    """Shown when the user has no habits yet."""
    return InlineKeyboardMarkup([
        [_btn("✨ Add my first habit", "addhabit")],
        [_btn("🏠 Main menu", "menu")],
    ])


def mood_keyboard_markup() -> InlineKeyboardMarkup:
    """Buttons 1-10 for the mood check-in, plus a cancel button."""
    rows = []
    row = []
    for number in range(1, 11):
        row.append(_btn(f"{number}", f"mood:{number}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    rows.append(row)
    rows.append([_btn("✖️ Cancel", "cancel_flow")])
    return InlineKeyboardMarkup(rows)


def mood_note_markup() -> InlineKeyboardMarkup:
    """Buttons shown after choosing a mood: skip the note, or cancel."""
    return InlineKeyboardMarkup([
        [_btn("⏭️ Skip the note", "mood_note_skip")],
        [_btn("✖️ Cancel", "cancel_flow")],
    ])


def confirm_delete_markup(habit_id: int, habit_name: str) -> InlineKeyboardMarkup:
    """'Are you sure?' buttons when deleting a habit."""
    return InlineKeyboardMarkup([
        [_btn(f"🗑️ Yes, delete '{habit_name}'", f"hdelc:{habit_id}")],
        [_btn("↩️ No, keep it", "hdelx")],
    ])


def reminders_markup(enabled: bool) -> InlineKeyboardMarkup:
    """Buttons for the reminders / settings screen."""
    toggle = [_btn("⏸️ Pause reminders", "remtoggle")] if enabled else [_btn("▶️ Resume reminders", "remtoggle")]
    rows = [
        [_btn("⏰ Set reminder time", "settime")],
        [_btn("🌍 Change time zone", "settz")],
        toggle,
        [_btn("🏠 Main menu", "menu")],
    ]
    return InlineKeyboardMarkup(rows)


def timezone_markup() -> InlineKeyboardMarkup:
    """A grid of common UTC offsets to pick from."""
    offsets = [-12, -11, -10, -9, -8, -7, -6, -5, -4, 0, 1, 2, 3, 4, 5, 5.5, 6, 7, 8, 9, 10]
    rows = []
    for i in range(0, len(offsets), 3):
        chunk = offsets[i : i + 3]
        rows.append([_btn(utils_label(o), f"tz:{o}") for o in chunk])
    rows.append([_btn("🏠 Main menu", "menu")])
    return InlineKeyboardMarkup(rows)


def utils_label(offset: float) -> str:
    """Local helper to label a timezone button, e.g. 1 -> 'UTC+1'."""
    from utils import format_offset  # imported here to avoid a circular import
    return format_offset(offset)


def cancel_button() -> InlineKeyboardMarkup:
    """A cancel button used during 'type your answer' flows."""
    return InlineKeyboardMarkup([[_btn("✖️ Cancel", "cancel_flow")]])