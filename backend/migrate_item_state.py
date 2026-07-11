import os

import psycopg2


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
        cur.execute("ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS direction VARCHAR(20)")
        cur.execute("ALTER TABLE lost_items ALTER COLUMN direction SET DEFAULT 'lost'")
        cur.execute("ALTER TABLE lost_items ALTER COLUMN status SET DEFAULT 'active'")

        cur.execute(
            """
            UPDATE lost_items
            SET direction = CASE
                WHEN status IN ('lost', 'found') THEN status
                WHEN item_type IN ('lost', 'found') THEN item_type
                WHEN direction IN ('lost', 'found') THEN direction
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
                WHEN status IN ('matched', 'closed') THEN 'recovered'
                ELSE 'active'
            END
            WHERE status IS NULL OR status NOT IN ('active', 'recovered', 'expired')
            """
        )

        cur.execute("ALTER TABLE lost_items ALTER COLUMN direction SET NOT NULL")
        cur.execute("ALTER TABLE lost_items ALTER COLUMN status SET NOT NULL")
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'lost_items_direction_check'
                ) THEN
                    ALTER TABLE lost_items
                    ADD CONSTRAINT lost_items_direction_check
                    CHECK (direction IN ('lost', 'found'));
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'lost_items_status_check'
                ) THEN
                    ALTER TABLE lost_items
                    ADD CONSTRAINT lost_items_status_check
                    CHECK (status IN ('active', 'recovered', 'expired'));
                END IF;
            END $$;
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_items_direction ON lost_items(direction)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_items_status ON lost_items(status)")
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
