"""Database connection and CRUD operations for 75 Hard Challenge tracker."""

import os
from contextlib import contextmanager
from typing import Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or not DATABASE_URL.strip():
    raise ValueError("DATABASE_URL must be set in .env. Copy .env.example to .env and set your PostgreSQL connection string.")


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor():
    """Context manager for database cursor with RealDictCursor."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur


# --- User operations ---


def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    """Fetch user by username."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, username, password_hash, display_name, created_at, COALESCE(xp, 0) AS xp, COALESCE(level, 1) AS level FROM users WHERE username = %s",
            (username,),
        )
        return cur.fetchone()


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    """Fetch user by id."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, username, display_name, created_at, COALESCE(xp, 0) AS xp, COALESCE(level, 1) AS level FROM users WHERE id = %s",
            (user_id,),
        )
        return cur.fetchone()


def list_users() -> list[dict[str, Any]]:
    """List all users (for dashboard selector)."""
    with get_cursor() as cur:
        cur.execute("SELECT id, username, display_name, COALESCE(xp, 0) AS xp, COALESCE(level, 1) AS level FROM users ORDER BY id")
        return cur.fetchall()


def update_user_xp_level(user_id: int, xp: int, level: int) -> None:
    """Update user XP and level."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE users SET xp = %s, level = %s WHERE id = %s",
            (xp, level, user_id),
        )


# --- Achievements ---


def get_achievements_for_user(user_id: int) -> list[dict[str, Any]]:
    """Get all achievements for a user."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, user_id, badge_type, earned_at FROM achievements WHERE user_id = %s ORDER BY earned_at DESC",
            (user_id,),
        )
        return cur.fetchall()


def insert_achievement(user_id: int, badge_type: str) -> Optional[dict[str, Any]]:
    """Insert achievement if not already earned. Returns row if inserted, None if duplicate."""
    with get_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO achievements (user_id, badge_type)
                VALUES (%s, %s)
                ON CONFLICT (user_id, badge_type) DO NOTHING
                RETURNING id, user_id, badge_type, earned_at
                """,
                (user_id, badge_type),
            )
            return cur.fetchone()
        except Exception:
            return None


def create_user(username: str, password_hash: str, display_name: str) -> dict[str, Any]:
    """Create a new user."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, display_name)
            VALUES (%s, %s, %s)
            RETURNING id, username, display_name, created_at
            """,
            (username, password_hash, display_name),
        )
        return cur.fetchone()


# --- Daily log operations ---


def get_log(user_id: int, log_date: str) -> Optional[dict[str, Any]]:
    """Get daily log for a user and date (log_date as YYYY-MM-DD)."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, log_date, breakfast, lunch, dinner,
                   workout_1, workout_1_duration, workout_2, workout_2_duration,
                   water_intake, reading_time, notes, created_at, updated_at
            FROM daily_logs
            WHERE user_id = %s AND log_date = %s
            """,
            (user_id, log_date),
        )
        return cur.fetchone()


def upsert_log(
    user_id: int,
    log_date: str,
    breakfast: Optional[str] = None,
    lunch: Optional[str] = None,
    dinner: Optional[str] = None,
    workout_1: Optional[str] = None,
    workout_1_duration: Optional[int] = None,
    workout_2: Optional[str] = None,
    workout_2_duration: Optional[int] = None,
    water_intake: Optional[float] = None,
    reading_time: Optional[int] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Insert or update daily log."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO daily_logs (
                user_id, log_date, breakfast, lunch, dinner,
                workout_1, workout_1_duration, workout_2, workout_2_duration,
                water_intake, reading_time, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, log_date)
            DO UPDATE SET
                breakfast = EXCLUDED.breakfast,
                lunch = EXCLUDED.lunch,
                dinner = EXCLUDED.dinner,
                workout_1 = EXCLUDED.workout_1,
                workout_1_duration = EXCLUDED.workout_1_duration,
                workout_2 = EXCLUDED.workout_2,
                workout_2_duration = EXCLUDED.workout_2_duration,
                water_intake = EXCLUDED.water_intake,
                reading_time = EXCLUDED.reading_time,
                notes = EXCLUDED.notes,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, user_id, log_date, breakfast, lunch, dinner,
                      workout_1, workout_1_duration, workout_2, workout_2_duration,
                      water_intake, reading_time, notes, created_at, updated_at
            """,
            (
                user_id,
                log_date,
                breakfast or None,
                lunch or None,
                dinner or None,
                workout_1 or None,
                workout_1_duration,
                workout_2 or None,
                workout_2_duration,
                water_intake,
                reading_time,
                notes or None,
            ),
        )
        return cur.fetchone()


def get_logs_for_user(
    user_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 365,
) -> list[dict[str, Any]]:
    """Get daily logs for a user, optionally filtered by date range."""
    with get_cursor() as cur:
        query = """
            SELECT id, user_id, log_date, breakfast, lunch, dinner,
                   workout_1, workout_1_duration, workout_2, workout_2_duration,
                   water_intake, reading_time, notes, created_at, updated_at
            FROM daily_logs
            WHERE user_id = %s
        """
        params: list[Any] = [user_id]
        if from_date:
            query += " AND log_date >= %s"
            params.append(from_date)
        if to_date:
            query += " AND log_date <= %s"
            params.append(to_date)
        query += " ORDER BY log_date DESC LIMIT %s"
        params.append(limit)
        cur.execute(query, params)
        return cur.fetchall()
