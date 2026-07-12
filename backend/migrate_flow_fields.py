import os

import psycopg2


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


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS storage_location VARCHAR(200)")
        cur.execute("ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS contact_visibility VARCHAR(20)")
        cur.execute("ALTER TABLE lost_items ALTER COLUMN contact_visibility SET DEFAULT 'private'")
        cur.execute(
            """
            UPDATE lost_items
            SET contact_visibility = CASE
                WHEN contact_visibility IN ('private', 'logged_in', 'claimed', 'public') THEN contact_visibility
                ELSE 'private'
            END
            WHERE contact_visibility IS NULL
               OR contact_visibility NOT IN ('private', 'logged_in', 'claimed', 'public')
            """
        )
        cur.execute("ALTER TABLE lost_items ALTER COLUMN contact_visibility SET NOT NULL")

        if not constraint_exists(cur, "lost_items_contact_visibility_check"):
            cur.execute(
                """
                ALTER TABLE lost_items
                ADD CONSTRAINT lost_items_contact_visibility_check
                CHECK (contact_visibility IN ('private', 'logged_in', 'claimed', 'public'))
                """
            )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(200) NOT NULL,
                message TEXT,
                notification_type VARCHAR(50) DEFAULT 'system',
                related_item_id INTEGER REFERENCES lost_items(id) ON DELETE SET NULL,
                link_url VARCHAR(500),
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS claim_requests (
                id SERIAL PRIMARY KEY,
                item_id INTEGER NOT NULL REFERENCES lost_items(id) ON DELETE CASCADE,
                requester_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                request_type VARCHAR(20) NOT NULL DEFAULT 'claim',
                requester_name VARCHAR(100) NOT NULL,
                requester_contact VARCHAR(200) NOT NULL,
                message TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'submitted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT claim_requests_type_check CHECK (request_type IN ('claim', 'contact')),
                CONSTRAINT claim_requests_status_check CHECK (status IN ('submitted', 'completed', 'rejected')),
                CONSTRAINT claim_requests_unique_user_item_type UNIQUE (item_id, requester_user_id, request_type)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lost_items_contact_visibility ON lost_items(contact_visibility)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_claim_requests_item_id ON claim_requests(item_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_claim_requests_requester ON claim_requests(requester_user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_claim_requests_owner ON claim_requests(owner_user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_claim_requests_created_at ON claim_requests(created_at)")

        conn.commit()
        print("Flow fields migration completed.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
