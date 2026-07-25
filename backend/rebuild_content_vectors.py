"""Rebuild every item vector without location or time information."""

import psycopg2.extras

from app import _build_vector, _lost_items_vector_column_exists
from db import get_db_connection, release_db_connection


def main() -> None:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    updated = 0
    skipped = 0
    try:
        if not _lost_items_vector_column_exists(cur):
            print("lost_items.vector column does not exist; install pgvector/apply schema before rebuilding item vectors.")
            return
        cur.execute("SELECT id, item_name, description, image_url FROM lost_items ORDER BY id")
        items = cur.fetchall()
        for item in items:
            vector = _build_vector(
                item["item_name"],
                description=item["description"],
                image_url=item["image_url"],
            )
            if not vector:
                skipped += 1
                continue
            cur.execute(
                "UPDATE lost_items SET vector = %s::vector, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (vector, item["id"]),
            )
            updated += 1
        conn.commit()
        print(f"Rebuilt {updated} content-only vectors; skipped {skipped} records.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)


if __name__ == "__main__":
    main()
