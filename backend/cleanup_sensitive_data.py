import argparse
import os

import psycopg2


DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "lostfound"),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}

DEFAULT_RETENTION_DAYS = int(os.environ.get("CONTACT_RETENTION_DAYS", "90"))


def cleanup_sensitive_data(retention_days: int, dry_run: bool = False) -> dict:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TEMP TABLE cleanup_expired_item_ids (
                id INTEGER PRIMARY KEY
            ) ON COMMIT DROP
            """
        )
        cur.execute(
            """
            INSERT INTO cleanup_expired_item_ids (id)
            SELECT id
            FROM lost_items
            WHERE status IN ('recovered', 'expired')
              AND COALESCE(updated_at, created_at) < CURRENT_TIMESTAMP - (%s || ' days')::interval
            """,
            (retention_days,),
        )

        cur.execute(
            """
            UPDATE lost_items
            SET contact_person = '已清理',
                contact_phone = NULL,
                contact_qq = NULL,
                contact_email = NULL,
                storage_location = NULL,
                contact_visibility = 'private',
                updated_at = CURRENT_TIMESTAMP
            WHERE id IN (SELECT id FROM cleanup_expired_item_ids)
              AND (
                contact_person IS DISTINCT FROM '已清理'
                OR contact_phone IS NOT NULL
                OR contact_qq IS NOT NULL
                OR contact_email IS NOT NULL
                OR storage_location IS NOT NULL
                OR contact_visibility IS DISTINCT FROM 'private'
              )
            """,
        )
        cleaned_items = cur.rowcount

        cur.execute(
            """
            UPDATE claim_requests
            SET requester_name = '已清理',
                requester_contact = '已清理',
                message = NULL
            WHERE item_id IN (SELECT id FROM cleanup_expired_item_ids)
              AND (
                requester_name IS DISTINCT FROM '已清理'
                OR requester_contact IS DISTINCT FROM '已清理'
                OR message IS NOT NULL
              )
            """,
        )
        cleaned_claims = cur.rowcount

        cur.execute(
            """
            UPDATE notifications
            SET message = NULL
            WHERE related_item_id IN (SELECT id FROM cleanup_expired_item_ids)
              AND message IS NOT NULL
            """,
        )
        cleaned_notifications = cur.rowcount

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

        return {
            "cleaned_items": cleaned_items,
            "cleaned_claims": cleaned_claims,
            "cleaned_notifications": cleaned_notifications,
            "dry_run": dry_run,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Clean old contact fields from completed or expired lost/found records.")
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.retention_days < 1:
        raise SystemExit("retention-days must be >= 1")

    result = cleanup_sensitive_data(args.retention_days, args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
