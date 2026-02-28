"""
Database Layer — PostgreSQL integration for Atlas stateful agent.

2 tables:
  short_term_memory — recent_messages (JSONB), current_cache (JSONB), expires_at
  long_term_memory  — facts (TEXT), recent_results (JSONB)

Safe to call init_database() multiple times (CREATE TABLE IF NOT EXISTS).
Called automatically by /api/health on first boot (Railway).
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Get PostgreSQL connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set in environment")
    return psycopg2.connect(database_url)


def init_database():
    """
    Create all tables if they don't exist.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    Called automatically by the /api/health endpoint on first boot.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS short_term_memory (
            user_id          TEXT PRIMARY KEY,
            recent_messages  JSONB NOT NULL DEFAULT '[]',
            current_cache    JSONB NOT NULL DEFAULT '{}',
            created_at       DATE NOT NULL DEFAULT CURRENT_DATE,
            expires_at       DATE NOT NULL DEFAULT CURRENT_DATE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS long_term_memory (
            user_id         TEXT PRIMARY KEY,
            facts           TEXT NOT NULL DEFAULT '',
            recent_results  JSONB NOT NULL DEFAULT '[]',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_short_term_expires_at ON short_term_memory (expires_at)")

    conn.commit()
    cursor.close()
    conn.close()
    print("[db] Tables initialised OK")
