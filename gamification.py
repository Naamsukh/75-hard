"""Gamification: XP, levels, badges, points, personal records."""

from datetime import date, timedelta
from typing import Any

from utils import completion_score, compute_streak, longest_streak_in_range


# --- XP & Levels ---

XP_PER_DAY_LOGGED = 10
XP_PER_FULL_DAY = 50
XP_BONUS_7_STREAK = 100
XP_BONUS_30_STREAK = 500

LEVEL_TITLES = {
    (1, 5): "Beginner",
    (6, 10): "Committed",
    (11, 20): "Champion",
    (21, 99): "Legend",
}


def _longest_streak_all(log_dates: list[date]) -> int:
    """Longest consecutive days with a log (anywhere in history)."""
    if not log_dates:
        return 0
    sorted_dates = sorted(set(log_dates))
    longest = 1
    current = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def _to_date(d) -> date:
    """Convert log_date value to date."""
    if isinstance(d, date):
        return d
    if hasattr(d, "date"):
        return d.date()
    return date.fromisoformat(str(d)[:10])


def calculate_xp(logs: list[dict], full_completion_count: int) -> int:
    """Total XP from logs: per day + full days + streak bonuses."""
    days_logged = len(logs)
    if not logs:
        return 0
    log_dates = [_to_date(l["log_date"]) for l in logs]
    best_streak = _longest_streak_all(log_dates)
    xp = days_logged * XP_PER_DAY_LOGGED + full_completion_count * XP_PER_FULL_DAY
    if best_streak >= 30:
        xp += XP_BONUS_30_STREAK
    if best_streak >= 7:
        xp += XP_BONUS_7_STREAK
    return xp


def xp_for_level(level: int) -> int:
    """Minimum XP required to be at this level (cumulative threshold)."""
    if level <= 0:
        return 0
    if level == 1:
        return 0
    if level <= 5:
        return (level - 1) * 100
    if level <= 10:
        return 500 + (level - 6) * 200
    if level <= 20:
        return 1500 + (level - 11) * 350
    return 5000 + max(0, (level - 21)) * 500


def get_level(xp: int) -> tuple[int, str]:
    """Return (level number, title) for given XP."""
    level = 1
    while level < 100 and xp >= xp_for_level(level + 1):
        level += 1
    for (lo, hi), title in LEVEL_TITLES.items():
        if lo <= level <= hi:
            return (level, title)
    return (level, "Legend")


def xp_progress_in_level(xp: int) -> tuple[int, int, int]:
    """Return (current_xp_in_level, xp_needed_for_level, level)."""
    level, _ = get_level(xp)
    base = xp_for_level(level)
    next_base = xp_for_level(level + 1)
    return (xp - base, next_base - base, level)


# --- Leaderboard points ---

POINTS_PER_DAY_LOGGED = 10
POINTS_PER_STREAK_DAY = 15
POINTS_PER_FULL_DAY = 50
POINTS_PER_100_WORKOUT_MIN = 10
POINTS_PER_LITER_WATER = 5
POINTS_PER_10_READING_MIN = 5


def calculate_points(metrics: dict[str, Any]) -> int:
    """Convert metrics to battle points (for leaderboard)."""
    days = metrics.get("days_logged", 0)
    streak = metrics.get("streak", 0)
    full = metrics.get("full_completion_days", 0)
    workout_min = metrics.get("total_workout_min", 0)
    water_L = metrics.get("total_water_L", 0)
    reading_min = metrics.get("total_reading_min", 0)
    pts = (
        days * POINTS_PER_DAY_LOGGED
        + streak * POINTS_PER_STREAK_DAY
        + full * POINTS_PER_FULL_DAY
        + (workout_min // 100) * POINTS_PER_100_WORKOUT_MIN
        + int(water_L * POINTS_PER_LITER_WATER)
        + (reading_min // 10) * POINTS_PER_10_READING_MIN
    )
    return pts


# --- Badges ---

BADGE_CRITERIA = [
    ("first_step", "First Step", "Log your first day", 1, "days_logged"),
    ("week_warrior", "Week Warrior", "7-day streak", 7, "streak"),
    ("month_master", "Month Master", "30-day streak", 30, "streak"),
    ("hydration_hero", "Hydration Hero", "100L total water", 100, "total_water_L"),
    ("reading_rookie", "Reading Rookie", "10 hours total reading", 600, "total_reading_min"),
    ("workout_wonder", "Workout Wonder", "1000 min total workout", 1000, "total_workout_min"),
    ("perfect_week", "Perfect Week", "7 consecutive full completion days", 7, "full_completion_streak"),
    ("75_hard_complete", "75 Hard Complete", "Complete 75 days", 75, "days_logged"),
]


def get_metrics_for_badges(logs: list[dict]) -> dict[str, Any]:
    """Compute metrics needed for badge checks."""
    if not logs:
        return {
            "days_logged": 0,
            "streak": 0,
            "total_water_L": 0,
            "total_reading_min": 0,
            "total_workout_min": 0,
            "full_completion_days": 0,
            "full_completion_streak": 0,
        }
    import pandas as pd
    df = pd.DataFrame(logs)
    df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
    log_dates = df["log_date"].tolist()
    streak = compute_streak(log_dates)
    full = df.apply(completion_score, axis=1).sum()
    w1 = pd.to_numeric(df["workout_1_duration"], errors="coerce").fillna(0)
    w2 = pd.to_numeric(df["workout_2_duration"], errors="coerce").fillna(0)
    workout_min = int((w1 + w2).sum())
    water_L = float(pd.to_numeric(df["water_intake"], errors="coerce").fillna(0).sum())
    reading_min = int(pd.to_numeric(df["reading_time"], errors="coerce").fillna(0).sum())
    # Full completion streak: longest run of consecutive full completion days
    df["full"] = df.apply(completion_score, axis=1)
    full_streak = 0
    if df["full"].any():
        df_sorted = df.sort_values("log_date")
        current = 0
        for v in df_sorted["full"]:
            if v:
                current += 1
                full_streak = max(full_streak, current)
            else:
                current = 0
    return {
        "days_logged": len(df),
        "streak": streak,
        "total_water_L": water_L,
        "total_reading_min": reading_min,
        "total_workout_min": workout_min,
        "full_completion_days": int(full),
        "full_completion_streak": full_streak,
    }


def check_achievements(metrics: dict[str, Any], already_earned: set[str]) -> list[str]:
    """Return list of badge_type that are newly earned (not in already_earned)."""
    newly_earned = []
    for badge_type, _name, _desc, threshold, key in BADGE_CRITERIA:
        if badge_type in already_earned:
            continue
        value = metrics.get(key, 0)
        if value is None:
            value = 0
        if value >= threshold:
            newly_earned.append(badge_type)
    return newly_earned


def get_badge_info(badge_type: str) -> tuple[str, str, str]:
    """Return (name, description, icon) for badge type."""
    icons = {
        "first_step": "⭐",
        "week_warrior": "🏆",
        "month_master": "👑",
        "hydration_hero": "💧",
        "reading_rookie": "📖",
        "workout_wonder": "🏋️",
        "perfect_week": "💎",
        "75_hard_complete": "🏅",
    }
    for bt, name, desc, _, _ in BADGE_CRITERIA:
        if bt == badge_type:
            return (name, desc, icons.get(bt, "🏆"))
    return (badge_type, "", "🏆")


# --- Personal records ---


def get_personal_records(logs: list[dict]) -> dict[str, Any]:
    """Best streak, max water in a day, max workout in a day, max reading, etc."""
    if not logs:
        return {
            "best_streak": 0,
            "max_water_L": 0,
            "max_workout_min": 0,
            "max_reading_min": 0,
            "total_days": 0,
            "full_completion_days": 0,
        }
    import pandas as pd
    df = pd.DataFrame(logs)
    df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
    log_dates = df["log_date"].tolist()
    best_streak = _longest_streak_all(log_dates)
    w1 = pd.to_numeric(df["workout_1_duration"], errors="coerce").fillna(0)
    w2 = pd.to_numeric(df["workout_2_duration"], errors="coerce").fillna(0)
    df["workout_min"] = w1 + w2
    water = pd.to_numeric(df["water_intake"], errors="coerce").fillna(0)
    reading = pd.to_numeric(df["reading_time"], errors="coerce").fillna(0)
    full = df.apply(completion_score, axis=1).sum()
    return {
        "best_streak": best_streak,
        "max_water_L": float(water.max()),
        "max_workout_min": int(df["workout_min"].max()),
        "max_reading_min": int(reading.max()),
        "total_days": len(df),
        "full_completion_days": int(full),
    }
