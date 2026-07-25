from pathlib import Path
import argparse
import json

from db import get_db_connection, release_db_connection
from support import SUPPORT_DOCS_DIR, import_support_knowledge


def main() -> None:
    parser = argparse.ArgumentParser(description="Import FoundIt support Markdown docs into the RAG knowledge base.")
    parser.add_argument("--docs-dir", default=str(SUPPORT_DOCS_DIR), help="Markdown docs directory")
    parser.add_argument("--force", action="store_true", help="Reimport unchanged files")
    args = parser.parse_args()

    conn = get_db_connection()
    try:
        stats = import_support_knowledge(conn, Path(args.docs_dir), force=args.force)
    finally:
        release_db_connection(conn)

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
