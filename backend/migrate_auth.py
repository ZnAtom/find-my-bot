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
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS casdoor_sub VARCHAR(200) UNIQUE")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS casdoor_name VARCHAR(200)")
        cur.execute("ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_items_user_id ON lost_items(user_id)")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
