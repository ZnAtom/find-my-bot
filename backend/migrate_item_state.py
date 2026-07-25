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


def constraint_exists(cur, name: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM pg_constraint
        WHERE conname = %s
        """,
        (name,),
    )
    return cur.fetchone() is not None


def column_exists(cur, column: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'lost_items' AND column_name = %s
        """,
        (column,),
    )
    return cur.fetchone() is not None


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        has_post_type = column_exists(cur, "post_type")

        cur.execute("ALTER TABLE lost_items DROP CONSTRAINT IF EXISTS lost_items_direction_check")
        cur.execute("ALTER TABLE lost_items DROP CONSTRAINT IF EXISTS lost_items_status_check")
        cur.execute("ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS direction VARCHAR(20)")
        cur.execute("ALTER TABLE lost_items ALTER COLUMN direction SET DEFAULT 'lost'")
        cur.execute("ALTER TABLE lost_items ALTER COLUMN status SET DEFAULT 'active'")

        if has_post_type:
            cur.execute(
                """
                UPDATE lost_items
                SET direction = CASE
                    WHEN direction IN ('lost', 'found') THEN direction
                    WHEN post_type IN ('lost', 'found') THEN post_type
                    WHEN status IN ('lost', 'found') THEN status
                    ELSE 'lost'
                END
                WHERE direction IS NULL OR direction NOT IN ('lost', 'found')
                """
            )
        else:
            cur.execute(
                """
                UPDATE lost_items
                SET direction = CASE
                    WHEN direction IN ('lost', 'found') THEN direction
                    WHEN status IN ('lost', 'found') THEN status
                    ELSE 'lost'
                END
                WHERE direction IS NULL OR direction NOT IN ('lost', 'found')
                """
            )

        cur.execute(
            """
            UPDATE lost_items
            SET status = CASE
                WHEN status IN ('active', 'recovered', 'expired') THEN status
                WHEN status IN ('lost', 'found', 'pending') THEN 'active'
                WHEN status IN ('matched', 'closed', 'resolved') THEN 'recovered'
                ELSE 'active'
            END
            WHERE status IS NULL OR status NOT IN ('active', 'recovered', 'expired')
            """
        )

        cur.execute("ALTER TABLE lost_items ALTER COLUMN direction SET NOT NULL")
        cur.execute("ALTER TABLE lost_items ALTER COLUMN status SET NOT NULL")

        if not constraint_exists(cur, "lost_items_direction_check"):
            cur.execute(
                """
                ALTER TABLE lost_items
                ADD CONSTRAINT lost_items_direction_check
                CHECK (direction IN ('lost', 'found'))
                """
            )
        if not constraint_exists(cur, "lost_items_status_check"):
            cur.execute(
                """
                ALTER TABLE lost_items
                ADD CONSTRAINT lost_items_status_check
                CHECK (status IN ('active', 'recovered', 'expired'))
                """
            )

        cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_items_direction ON lost_items(direction)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_items_status ON lost_items(status)")
        cur.execute("DROP INDEX IF EXISTS idx_lost_items_post_type")
        conn.commit()
        print("Item state migration completed.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
