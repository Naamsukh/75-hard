# 75 Hard Challenge Tracker

A Streamlit app to track meals, workouts, water intake, reading time, and notes for the 75 Hard Challenge. Built for two users with a shared Neon PostgreSQL database.

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**

   Copy `.env.example` to `.env` and set your PostgreSQL connection string:

   ```bash
   copy .env.example .env
   ```
   (On macOS/Linux use `cp .env.example .env`.)

   Edit `.env` and set `DATABASE_URL=postgresql://...` (e.g. your Neon connection string). `.env` is gitignored; do not commit it.

3. **Initialize the database**

   Creates tables and the two user accounts (if you have `init_db.py`):

   ```bash
   python init_db.py
   ```

4. **Run gamification migration** (adds XP, level, achievements)

   ```bash
   python migrate_gamification.py
   ```

5. **Run the app**

   ```bash
   streamlit run app.py
   ```

## Login credentials

| Username | Password       | Display name    |
|----------|----------------|-----------------|
| `user1`  | `Challenge75!` | You             |
| `user2`  | `Strong75!`    | User2  |

Use these to log in. You can change display names or passwords later by updating the database.

## Features

- **Daily Tracker** – Log breakfast, lunch, dinner; two workouts (type + duration); water (liters); reading time (minutes); and notes. Pick any date to view or edit.
- **Dashboard** – Gamified progress: level and XP bar, badges, streak, 75-day activity calendar, personal records, water/reading/workout charts, and recent 7-day table.
- **Leaderboard** – Battle score (points), comparison chart, radial progress, head-to-head metrics for last 7 days, 30 days, or overall.
- **Challenges** – Weekly challenges (hydration 21L, consistency 7 days, intensity 500 min) and daily bonus goals (Morning Logger, Overachiever).

## Tech stack

- Streamlit, PostgreSQL (Neon), psycopg2, pandas, plotly, bcrypt, python-dotenv.
