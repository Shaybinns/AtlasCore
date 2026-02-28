"""
Run once to create Atlas memory tables in Postgres (e.g. on Railway).
Set DATABASE_URL in environment, then: python scripts/init_db.py
"""
import os
import sys

# Project root on path so imports work if run from repo root or scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def main():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set. Set it (e.g. from Railway) and try again.")
        sys.exit(1)

    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations", "001_atlas_memory_schema.sql")
    with open(sql_path, "r") as f:
        sql = f.read()

    import psycopg2
    conn = psycopg2.connect(url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        print("Atlas memory schema applied successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
