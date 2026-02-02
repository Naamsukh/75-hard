"""One-time migration: add XP, level to users and create achievements table."""

import sys

import psycopg2
from database import DATABASE_URL


def run_sql(conn, sql: str, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params or ())


def main():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        # Add xp and level to users if not exist
        run_sql(conn, """
            ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0;
        """)
        run_sql(conn, """
            ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1;
        """)
        conn.commit()

        # Create achievements table
        run_sql(conn, """
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                badge_type VARCHAR(50),
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, badge_type)
            );
        """)
        conn.commit()
        print("Gamification migration completed.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
