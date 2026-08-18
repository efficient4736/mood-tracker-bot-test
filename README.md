# Habit & Mood Companion 🤖💛

A warm, private Telegram bot that helps you build habits, track your mood, and
get gentle (never guilt-trippy) daily reminders. Everything runs on **your own
machine or hosting** — no third-party cloud, no data leaving your control.

It was written for people who are **not programmers**. The code is clean,
heavily commented, and everything is explained below step by step.

---

## Table of contents

1. [What the bot does](#what-the-bot-does)
2. [How it looks and feels (sample dialogue)](#sample-dialogue)
3. [The commands](#commands)
4. [Project structure](#project-structure)
5. [Step 1 — Create your bot with BotFather](#step-1--create-your-bot-with-botfather)
6. [Step 2 — Install Python](#step-2--install-python)
7. [Step 3 — Set up and run locally](#step-3--set-up-and-run-locally)
   - [Windows](#windows)
   - [Mac / Linux](#mac--linux)
8. [Step 4 — Set your time zone](#step-4--set-your-time-zone)
9. [How reminders work](#how-reminders-work)
10. [Running 24/7 — deploy it for free](#running-247--deploy-it-for-free)
    - [Railway](#railway-recommended)
    - [Render](#render)
    - [Fly.io](#flyio)
11. [How to keep it running on your own computer](#keep-it-running-on-your-own-computer)
12. [Troubleshooting](#troubleshooting)
13. [Where your data lives](#where-your-data-lives)
14. [Extending the bot](#extending-the-bot)

---

## What the bot does

- **Habit tracking.** Add habits like "Gym", "Read 20 pages" or "No sugar".
  Mark them done with a single tap (or `/done Gym`). See your current streak,
  your longest streak, and a weekly + monthly completion overview.
- **Mood tracking.** Log how you feel each day on a scale of 1–10, with an
  optional short note. See your weekly average and whether the trend is up, down
  or steady.
- **Gentle accountability.** Pick a reminder time (e.g. `20:00`). At that time
  the bot sends a friendly evening check-in listing what's still undone — with
  no pressure and no judgement. It also celebrates when you hit streak
  milestones (3, 7, 14, 21, 30, 60, 90, 180 and 365 days).
- **Pause reminders** any time (e.g. holidays) and resume later.
- **Statistics.** One `/stats` screen shows streaks, completion rates, mood
  average and trend, plus a small text-based mood chart.
- **Privacy by design.** A single-user bot: only you and your bot can talk to
  each other. All data lives in a local SQLite file on *your* hosting.

---

## Sample dialogue

> **You:** `/start`
>
> **Bot:**
> ```
> Hey Alex! 👋 Welcome to Habit & Mood Companion.
>
> I'm here to help you build habits and keep tabs on how you're
> feeling — with zero pressure and lots of encouragement. 💛
>
> Here's how it works:
> • Add a few habits with /addhabit
> • Tick them off each day with /done
> • Log a quick mood with /mood
> • Watch your streaks and stats grow with /stats
>
> Everything you share stays on *your* machine — no cloud, no snooping.
> ```
> *(buttons appear under the message: 📋 My habits · ✨ Add a habit ·
> 😊 Log my mood · 📊 My stats · ⏰ Reminders · ❓ Help)*

> **You:** tap **✨ Add a habit** → type `Gym`
>
> **Bot:**
> ```
> Added Gym to your habits! 🎉
>
> You can mark it done today with the buttons in /habits,
> or just type /done Gym.
> ```

> **You:** `/done Gym`
>
> **Bot:**
> ```
> Gym done for today! ✅
>
> Nice, Gym is on a 1-day streak! 🔥
> ```

> **You:** tap **😊 Log my mood**
>
> **Bot:** `How are you feeling today? 😊 Pick a number from 1 (really low) to 10 (fantastic).`
>
> *(buttons: 1 2 3 4 5 / 6 7 8 9 10 / ✖️ Cancel)*
>
> **You:** tap `8`
>
> **Bot:**
> ```
> Got it — 8/10 🤩
> Want to add a short note about why? (Optional — just type it, or skip.)
> ```
> **You:** `Great workout, sunny day`
>
> **Bot:**
> ```
> Logged 8/10 🤩 with a note. 💛
> Thanks for checking in — that great feeling is totally valid. See you tomorrow!
> ```

> **You:** `/stats`
>
> **Bot:**
> ```
> 📊 Your stats
>
> 🔥 Streaks
> · Gym: 4 day(s) 🔥 (best: 4)
> · Read 20 pages: 2 day(s) (best: 5)
>
> ✅ Done today: 2/2
>
> 📅 Completion — last 7 days
> · Gym: 4/7 (57%)
> · Read 20 pages: 2/7 (29%)
> Overall this week: 43%
>
> 🗓️ Completion — this month
> · Gym: 9/18 (50%)
> · Read 20 pages: 6/18 (33%)
> Overall this month: 42%
>
> 😊 Mood — last 7 days
> · Mon 08-17  7/10  ▓▓▓▓▓▓▓░░░
> · Tue 08-18  8/10  ▓▓▓▓▓▓▓▓░░
> Average mood: 7.5/10 — rising 📈
>
> 🏆 Longest streak ever: 5 day(s) — Read 20 pages
> ```

> **Bot (at 20:00, if you haven't finished everything):**
> ```
> Hey Alex 💛 Quick evening check-in.
> Here's where things stand today:
>   · Read 20 pages (streak 2)
>
> No pressure — just a friendly nudge. 😊
> ```
> *(buttons: ✅ Read 20 pages · 😊 Log my mood · 🏠 Main menu)*

> **Bot (when you hit 7 days on a habit):**
> ```
> One whole week of Gym! 🙌 That's a real habit now. So proud of you.
> ```

---

## Commands

| Command       | What it does                                                        |
|---------------|---------------------------------------------------------------------|
| `/start`      | Welcome message + main menu.                                        |
| `/habits`     | Your habits with status, streaks, and Done / Undo / Rename / Delete buttons. |
| `/addhabit`   | Add a habit. Works as `/addhabit Gym` or plain `/addhabit` (the bot then asks). |
| `/done`       | Mark a habit done. Works as `/done` (shows buttons) or `/done Gym`. |
| `/mood`       | Quick mood check-in (tap 1–10, optional note).                      |
| `/stats`      | Streaks, completion rates, mood average, trend, longest streak.     |
| `/reminders`  | Set reminder time, pause/resume, change time zone.                  |
| `/settings`   | Same as reminders (time zone and such).                             |
| `/help`       | Shows this list.                                                    |
| `/cancel`     | Stops whatever multi-step flow you're in.                           |

Everything also works through the on-screen buttons, so you rarely need to
type a command at all.

---

## Project structure

```
moodbot/
├── main.py              ← START HERE. Runs the bot.
├── config.py            ← Reads your token and settings from .env.
├── database.py          ← All SQLite storage (habits, logs, moods...).
├── utils.py             ← Dates, time zones, streaks, celebrations.
├── keyboards.py         ← All the button layouts.
├── requirements.txt     ← The libraries the bot needs.
├── .env.example         ← Template for your secret settings.
├── .gitignore           ← Keeps secrets/data out of git.
├── handlers/
│   ├── commands.py      ← /start, /help, /habits, /done, /stats...
│   ├── flows.py         ← Multi-step conversations (add habit, mood...).
│   ├── callbacks.py     ← What happens when you tap a button.
│   ├── messages.py      ← The text + buttons for common screens.
│   └── reminders.py     ← The daily reminder job.
└── data/                ← Created automatically. Holds moodbot.db.
```

---

## Step 1 — Create your bot with BotFather

1. Open Telegram and search for **@BotFather** (the official bot that makes bots).
2. Start a chat and send `/newbot`.
3. Choose a **display name**, e.g. `Habit & Mood Companion`.
4. Choose a **username** ending in `bot`, e.g. `alex_mood_bot`.
5. BotFather replies with an API token that looks like:
   `1234567890:AAE...sOMeLoNgStRiNg`
6. Copy that token — it's your bot's only password. **Keep it secret.**

> 💡 Find your bot later by searching its username in Telegram and pressing
> **Start**. From then on it's private: only you can message it.

---

## Step 2 — Install Python

You need Python **3.11 or newer**.

- **Windows:** download from [python.org](https://www.python.org/downloads/).
  In the installer, tick **"Add python.exe to PATH"** before installing.
- **Mac:** download from python.org, or run `brew install python`.
- **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install python3 python3-pip python3-venv`

Check it worked by opening a terminal and running:

```
python --version
```

You should see `Python 3.11.x` or higher.

---

## Step 3 — Set up and run locally

### Windows

1. Open **PowerShell** (Start menu → type "PowerShell").
2. Go into the project folder:
   ```
   cd Downloads\moodbot
   ```
3. Create a virtual environment (an isolated copy of Python for this project):
   ```
   python -m venv .venv
   ```
4. Activate it:
   ```
   .\.venv\Scripts\Activate.ps1
   ```
   > If that fails with a "running scripts is disabled" error, run once:
   > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
   > and try again.
5. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
6. Create your settings file:
   ```
   Copy-Item .env.example .env
   ```
7. Open `.env` in Notepad (right-click → Open with → Notepad) and paste your
   BotFather token after `BOT_TOKEN=`.
8. Start the bot:
   ```
   python main.py
   ```
   You should see log lines like `Starting Habit & Mood Companion...`.
   Leave the window open — that's what keeps the bot running. Press **Ctrl+C**
   to stop it.

### Mac / Linux

Open **Terminal** and run:

```
cd Downloads/moodbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then open `.env` in your editor, paste your token after `BOT_TOKEN=`, and run:

```
python main.py
```

> If you get a "python: command not found" error, try `python3` instead.

---

## Step 4 — Set your time zone

The bot needs to know your time zone to (a) know what "today" means and
(b) send reminders at the right moment.

1. Send `/reminders` (or `/settings`).
2. Tap **🌍 Change time zone**.
3. Pick the **UTC offset** closest to you, or type it directly, e.g. `UTC+2`,
   `+2`, `-5`, `-5.5`.

Quick reference for common places:

| Place                 | Offset  |
|-----------------------|---------|
| New York / Toronto    | UTC-5   |
| Mexico City           | UTC-6   |
| Los Angeles / Vancouver | UTC-8  |
| London                | UTC+0   |
| Berlin / Paris / Rome | UTC+1   |
| Istanbul / Athens     | UTC+2   |
| Moscow / Nairobi      | UTC+3   |
| Dubai                 | UTC+4   |
| India                 | UTC+5.5 |
| Bangkok / Jakarta     | UTC+7   |
| Hong Kong / Singapore | UTC+8   |
| Tokyo                 | UTC+9   |
| Sydney                | UTC+10  |

> ⚠️ These are **winter** offsets. If your country uses daylight saving time,
> you may need to change the offset twice a year (spring and autumn), because
> the bot intentionally keeps it simple and does not follow DST automatically.

---

## How reminders work

1. Send `/reminders`.
2. Tap **⏰ Set reminder time** and type a time in 24-hour format, e.g. `20:00`
   or `09:30`.
3. Reminders turn on automatically. Every day at that time (your time zone)
   you'll get a gentle evening check-in.
4. To stop them temporarily (holidays, busy weeks), use **⏸️ Pause reminders**.
   The same button says **▶️ Resume reminders** afterwards.

The bot checks every minute, so it will always fire at your exact time.

---

## Running 24/7 — deploy it for free

Your computer must be switched off at some point, so for true 24/7 the bot
needs a small cloud server. All three options below have a **free tier** and
are point-and-click. Pick **Railway** if you're not sure.

Before you start: make sure your code is in a git repository (it already is)
and pushed to GitHub/GitLab, because these services deploy straight from there.

### Railway (recommended)

1. Go to [railway.app](https://railway.app) and sign up (GitHub login).
2. Click **New Project → Deploy from GitHub repo** and pick your `moodbot` repo.
3. Railway auto-detects Python. Add a start command:
   - Open the project → **Settings** tab → find **Start Command**.
   - Set it to: `python main.py`
4. Add your secret:
   - **Variables** tab → **New Variable** → `BOT_TOKEN` = your token.
5. Railway deploys automatically. Watch the **Deployments** tab — you should
   see it go green. Your bot is now online 24/7. 🎉

### Render

1. Go to [render.com](https://render.com) and sign up (GitHub login).
2. Click **New → Web Service** and connect your `moodbot` repo.
3. Fill in:
   - **Name:** `moodbot`
   - **Runtime:** `Python 3`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `python main.py`
4. Under **Environment**, add the secret: `BOT_TOKEN` = your token.
5. **Create Web Service.** Render builds and starts it. It's free, but the
   free web service sleeps after 15 minutes of inactivity — and it only
   "wakes" on web requests. Because Telegram uses long polling (the bot dials
   out to Telegram), a sleeping instance may not restart on its own. If you
   find reminders going quiet, the simplest fix is the **Starter** plan, or
   use Railway/Fly.io instead. You can also upgrade to Render's paid tier.

### Fly.io

1. Install the Fly CLI, then log in: `fly auth login`
2. In the project folder run:
   ```
   fly launch
   ```
   - Answer the prompts; let it use the default Dockerfile (it generates one).
   - Say **yes** when it asks to deploy.
3. Set your secret:
   ```
   fly secrets set BOT_TOKEN=your-token-here
   ```
4. Deploy:
   ```
   fly deploy
   ```
   Your app runs 24/7 on the free allowance (a small always-on VM).

> On every platform, your SQLite database lives inside the container. Free
> tiers use an ephemeral disk, so your habits/mood history may reset if the
> instance is rebuilt. For a personal bot this is usually fine, but if you want
> permanent history, the easiest upgrade is Railway (which persists disk data)
> or storing `data/` on a mounted volume.

---

## Keep it running on your own computer

If you prefer to run it on a machine you leave on:

- **Windows:** press **Win+R**, type `shell:startup`, and drop a shortcut to a
  `.bat` file that runs:
  ```bat
  cd /d C:\Users\YOURNAME\Downloads\moodbot
  .\.venv\Scripts\python.exe main.py
  ```
- **Mac / Linux:** use `tmux` (keeps it alive after you close the terminal):
  ```
  tmux new -s moodbot
  cd ~/Downloads/moodbot && python main.py
  # detach with Ctrl+B then D; come back with: tmux attach -t moodbot
  ```
  Or install `pm2` for auto-restart on crash.

---

## Troubleshooting

| Problem | Likely cause / fix |
|---------|--------------------|
| `No BOT_TOKEN found...` | You didn't create `.env` or didn't paste the token. Copy `.env.example` to `.env` and fill in `BOT_TOKEN`. |
| `Unauthorized` or `Conflict: terminated by other getUpdates request` | Wrong token, or the bot is running twice. Stop the other copy, and check you used the token from **your** BotFather. |
| `'python' is not recognized` | Python isn't on your PATH. Reinstall with "Add python.exe to PATH" ticked, or use `python3`. |
| `pip` command not found | You skipped activating the virtual environment. Activate it (see Step 3) and retry. |
| Bot starts but ignores me | Did you press **Start** in the chat with your bot? The bot only replies to you. |
| Reminders don't arrive | 1) Time zone is wrong — set the correct UTC offset. 2) Reminders are paused. 3) You never set a reminder time. Check all three in `/reminders`. |
| Reminder time seems off by an hour | Daylight saving time. Re-set your UTC offset in `/reminders`. |
| "That doesn't look like a valid time" | Use 24-hour format like `20:00`, not `8pm`. |
| Buttons do nothing | The bot crashed or restarted — check the logs. You can always just send `/start` again. |
| Bot stopped after I closed the terminal | Normal — see [Running 24/7](#running-247--deploy-it-for-free) or the tmux/startup tips. |
| Where are my logs? | Everything prints to the terminal where you run `python main.py`. Set `LOG_LEVEL=DEBUG` in `.env` for more detail. |
| `pip install` fails with an error about "job-queue" or APScheduler | Update pip first: `python -m pip install --upgrade pip`, then retry `pip install -r requirements.txt`. |

---

## Where your data lives

- One SQLite file: `data/moodbot.db` (created automatically).
- Tables: `users`, `habits`, `habit_logs`, `mood_logs`.
- **Back up** simply by copying that one file somewhere safe (or let your
  hosting provider's volume do it).
- Delete it to start completely fresh.

---

## Extending the bot

The code is intentionally modular:

- Add a new **command** → write a function in `handlers/commands.py` and
  register it in `main.py` (one line).
- Add a new **button flow** → add a keyboard in `keyboards.py`, handle the
  callback in `handlers/callbacks.py`, or add a step in `handlers/flows.py`.
- Add a new **stat** → edit `build_stats_text()` in `handlers/messages.py`.

Each file starts with a comment explaining what it does. Happy habits! 💛