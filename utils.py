"""Shared helpers for 75 Hard Challenge tracker (streak, completion)."""

import math
from datetime import date, timedelta
from typing import Any


def _to_number(val: Any, default: float = 0) -> float:
    """Coerce value to number; treat None and NaN as default."""
    if val is None:
        return default
    try:
        x = float(val)
        return default if math.isnan(x) else x
    except (TypeError, ValueError):
        return default


def completion_score(row: dict[str, Any]) -> bool:
    """True if day meets 75 Hard style: 2 workouts, water >= 3 L, reading >= 10 min."""
    w1 = (row.get("workout_1") or row.get("workout_1_duration")) is not None
    w2 = (row.get("workout_2") or row.get("workout_2_duration")) is not None
    water = _to_number(row.get("water_intake"), 0) >= 3.0
    reading = _to_number(row.get("reading_time"), 0) >= 10
    return w1 and w2 and water and reading


def compute_streak(log_dates: list[date]) -> int:
    """Current streak: consecutive days with a log, ending today or yesterday."""
    if not log_dates:
        return 0
    sorted_dates = sorted(set(log_dates), reverse=True)
    today = date.today()
    if sorted_dates[0] not in (today, today - timedelta(days=1)):
        return 0
    streak = 0
    expect = today
    for d in sorted_dates:
        if d == expect:
            streak += 1
            expect -= timedelta(days=1)
        else:
            break
    return streak


def longest_streak_in_range(
    log_dates: list[date],
    from_date: date,
    to_date: date,
) -> int:
    """Longest run of consecutive days with a log within the given date range."""
    if not log_dates:
        return 0
    in_range = sorted(
        d for d in set(log_dates)
        if from_date <= d <= to_date
    )
    if not in_range:
        return 0
    longest = 1
    current = 1
    for i in range(1, len(in_range)):
        if (in_range[i] - in_range[i - 1]).days == 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest
