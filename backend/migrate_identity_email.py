import os

import psycopg2

from config_env import load_project_env

load_project_env()

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "lostfound"),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS school_email VARCHAR(320)")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_email VARCHAR(320)")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS school_email_verified_at TIMESTAMP")
        cur.execute("ALTER TABLE claim_requests ADD COLUMN IF NOT EXISTS requester_school_email VARCHAR(320)")

        cur.execute(
            """
            UPDATE users
            SET contact_email = email
            WHERE contact_email IS NULL AND email IS NOT NULL
            """
        )
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_school_email_unique
            ON users(LOWER(school_email))
            WHERE school_email IS NOT NULL
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_claim_requests_school_email
            ON claim_requests(requester_school_email)
            """
        )
        conn.commit()
        print("Identity email migration completed.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
