"""Shared message builders.

Several places need the same messages: the /habits command, the buttons on the
habit list, the evening reminder, and /stats. Putting them here means we write
them once and reuse them everywhere. Each function returns (text, markup).
"""

from telegram import InlineKeyboardMarkup

import database
import keyboards
import utils


def main_menu_text() -> str:
    return "🏠 *Main menu* — what would you like to do?"


def help_text() -> str:
    return (
        "Here's everything I can do. 💛\n\n"
        "/start — see this again\n"
        "/habits — your habits with done/undo buttons\n"
        "/addhabit — add a new habit (e.g. /addhabit Gym)\n"
        "/done — mark a habit done. Use /done or /done Gym\n"
        "/mood — a quick mood check-in (1-10 + optional note)\n"
        "/stats — streaks, completion rates and mood trends\n"
        "/reminders — set your reminder time, pause or resume\n"
        "/settings — time zone and other settings\n"
        "/help — this list\n\n"
        "Tip: most things also work through the buttons, so you don't "
        "have to type commands at all. 😊"
    )


def build_habits_view(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """The full habit list: status, streak, and action buttons for each habit."""
    habits = database.get_habits(user_id)
    offset = database.get_timezone_offset(user_id)
    today = utils.local_today(offset)

    if not habits:
        return (
            "You don't have any habits yet. ✨\n\n"
            "Tap below to add your first one — something small and "
            "realistic that you'd love to keep up.",
            keyboards.empty_habits_markup(),
        )

    lines = ["📋 *Your habits*", ""]
    for index, habit in enumerate(habits, start=1):
        done = database.is_done(habit["id"], today)
        streak = database.current_streak(habit["id"], today)
        status = "✅ done today" if done else "⬜ not yet today"
        fire = " 🔥" if streak >= 3 else ""
        lines.append(f"{index}. {habit['name']}")
        lines.append(f"   {status} · streak {streak} day(s){fire}")
        lines.append("")

    text = "\n".join(lines).strip()
    return text, keyboards.habits_footer_markup()


def build_reminders_view(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """The reminders / settings screen."""
    user = database.get_user(user_id)
    time_text = user["reminder_time"] if user["reminder_time"] else "not set yet"
    state_text = "on" if user["reminders_enabled"] else "paused"
    zone_text = utils.format_offset(user["timezone_offset"])
    enabled = bool(user["reminders_enabled"])

    text = (
        "⏰ *Reminders*\n\n"
        f"Reminder time: {time_text}\n"
        f"Status: {state_text}\n"
        f"Time zone: {zone_text}\n\n"
        "At your reminder time I'll send a gentle evening check-in "
        "to help you wrap up the day. No guilt, ever — just a nudge."
    )
    return text, keyboards.reminders_markup(enabled)


def build_checkin(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """The evening reminder message: undone habits + a mood button."""
    user = database.get_user(user_id)
    name = (user or {}).get("first_name") or "friend"
    habits = database.get_habits(user_id)
    offset = database.get_timezone_offset(user_id)
    today = utils.local_today(offset)

    undone = [h for h in habits if not database.is_done(h["id"], today)]
    done = [h for h in habits if database.is_done(h["id"], today)]

    if not habits:
        text = (
            f"Hey {name} 💛 Just checking in. You don't have any habits yet — "
            "whenever you're ready, add one and we'll get rolling."
        )
        buttons = [[keyboards._btn("✨ Add a habit", "addhabit")],
                   [keyboards._btn("😊 Log my mood", "mood")]]
        return text, InlineKeyboardMarkup(buttons)

    if not undone:
        text = (
            f"Hey {name} 💛 Everything is done for today! "
            "That's a wonderful way to end the day. 🌟"
        )
    else:
        lines = [f"Hey {name} 💛 Quick evening check-in.",
                 "Here's where things stand today:"]
        for habit in undone:
            streak = database.current_streak(habit["id"], today)
            lines.append(f"  · {habit['name']} (streak {streak})")
        lines.append("")
        lines.append("No pressure — just a friendly nudge. 😊")
        text = "\n".join(lines)

    rows = [[keyboards._btn(f"✅ {h['name']}", f"hd:{h['id']}")] for h in undone]
    rows.append([keyboards._btn("😊 Log my mood", "mood"),
                 keyboards._btn("🏠 Main menu", "menu")])
    return text, InlineKeyboardMarkup(rows)


def build_stats_text(user_id: int) -> str:
    """The /stats report: streaks, completion rates, mood and trends."""
    offset = database.get_timezone_offset(user_id)
    today = utils.local_today(offset)
    week_start = utils.add_days(today, -6)          # last 7 days, including today
    m_start = utils.month_start(today)              # first day of this month
    month_days = int(today.split("-")[2])           # days elapsed this month

    habits = database.get_habits(user_id)

    if not habits:
        return (
            "There's not much to show yet. ✨\n\n"
            "Add your first habit with /addhabit and check back in a few days — "
            "then we'll have real streaks and stats!"
        )

    lines = ["📊 *Your stats*", ""]

    # --- Streaks ----------------------------------------------------------
    lines.append("🔥 *Streaks*")
    best_ever = 0
    best_name = ""
    for habit in habits:
        streak = database.current_streak(habit["id"], today)
        longest = database.longest_streak(habit["id"])
        fire = " 🔥" if streak >= 3 else ""
        lines.append(f"· {habit['name']}: {streak} day(s){fire} (best: {longest})")
        if longest > best_ever:
            best_ever = longest
            best_name = habit["name"]

    # --- Today ------------------------------------------------------------
    done_today = sum(1 for h in habits if database.is_done(h["id"], today))
    lines.append("")
    lines.append(f"✅ Done today: {done_today}/{len(habits)}")

    # --- Completion rates --------------------------------------------------
    lines.append("")
    lines.append("📅 *Completion — last 7 days*")
    total_done = 0
    for habit in habits:
        done7 = database.days_done_in_range(habit["id"], week_start, today)
        total_done += done7
        percent = round(done7 / 7 * 100)
        lines.append(f"· {habit['name']}: {done7}/7 ({percent}%)")
    week_percent = round(total_done / (len(habits) * 7) * 100)
    lines.append(f"Overall this week: {week_percent}%")

    lines.append("")
    lines.append("🗓️ *Completion — this month*")
    month_done = 0
    for habit in habits:
        done_m = database.days_done_in_range(habit["id"], m_start, today)
        month_done += done_m
        percent = round(done_m / max(month_days, 1) * 100)
        lines.append(f"· {habit['name']}: {done_m}/{month_days} ({percent}%)")
    month_percent = round(month_done / max(len(habits) * month_days, 1) * 100)
    lines.append(f"Overall this month: {month_percent}%")

    # --- Mood ---------------------------------------------------------------
    moods = database.get_moods_in_range(user_id, week_start, today)
    if moods:
        lines.append("")
        lines.append("😊 *Mood — last 7 days*")
        for row in moods:
            lines.append(
                f"· {utils.weekday_short(row['date'])} {row['date'][5:]}  "
                f"{utils.mood_emoji(row['mood'])} {row['mood']}/10  "
                f"{utils.mood_bar(row['mood'])}"
            )
        values = [r["mood"] for r in moods]
        avg = sum(values) / len(values)
        recent = [r["mood"] for r in moods if r["date"] >= utils.add_days(today, -2)]
        previous = [r["mood"] for r in moods if utils.add_days(today, -5) <= r["date"] <= utils.add_days(today, -3)]
        trend = utils.mood_trend(
            sum(previous) / len(previous) if previous else None,
            sum(recent) / len(recent) if recent else None,
        )
        lines.append(f"Average mood: {avg:.1f}/10 — {trend}")

    # --- Longest streak ever -----------------------------------------------
    if best_ever:
        lines.append("")
        lines.append(f"🏆 Longest streak ever: {best_ever} day(s) — {best_name}")

    return "\n".join(lines)