import psycopg2
import os

DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_NAME = os.environ.get("DB_NAME", "lostfound")
DB_HOST = os.environ.get("DB_HOST", "localhost")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    cur = conn.cursor()
    
    # Check if post_type column exists
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='lost_items' AND column_name='post_type'
    """)
    if not cur.fetchone():
        print("Adding post_type column...")
        cur.execute("ALTER TABLE lost_items ADD COLUMN post_type VARCHAR(20) DEFAULT 'lost'")
        
        # Migrate data
        print("Migrating status to post_type...")
        cur.execute("UPDATE lost_items SET post_type = status, status = 'pending' WHERE status IN ('lost', 'found')")
        
    conn.commit()
    cur.close()
    conn.close()
    print("Migration post_type complete.")
except Exception as e:
    print(f"Migration error: {e}")
