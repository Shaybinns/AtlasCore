"""
Short-term memory: recent conversation + current cache for stateful agent.
Postgres-backed; use DATABASE_URL (e.g. Railway).
"""
import psycopg2
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from dotenv import load_dotenv
load_dotenv()

SHORT_TERM_DB = "short_term_memory"
MAX_RECENT_MESSAGES = 20
EXPIRY_HOURS = 24


def get_db_connection():
    """Connection using Railway-injected DATABASE_URL."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def add_to_recent_conversation(user_id: str, message: str) -> bool:
    """Append message; keep last MAX_RECENT_MESSAGES; extend expiry to 24h."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT recent_messages, current_cache, created_at FROM {SHORT_TERM_DB} WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            messages = list(row[0])
            current_cache = row[1] or {}
            created_at = row[2]
        else:
            messages = []
            current_cache = {}
            created_at = datetime.now().date()
        messages.append(message)
        if len(messages) > MAX_RECENT_MESSAGES:
            messages = messages[-MAX_RECENT_MESSAGES:]
        expires_at = (datetime.now() + timedelta(hours=EXPIRY_HOURS)).date()
        if row is not None:
            cursor.execute(
                f"UPDATE {SHORT_TERM_DB} SET recent_messages = %s, expires_at = %s WHERE user_id = %s",
                (json.dumps(messages), expires_at, user_id),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {SHORT_TERM_DB} (user_id, recent_messages, current_cache, created_at, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, json.dumps(messages), json.dumps(current_cache), created_at, expires_at),
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error add_to_recent_conversation: {e}")
        return False


def get_recent_conversation(user_id: str) -> str:
    """Return recent messages as newline-separated text; empty if expired or missing."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT recent_messages FROM {SHORT_TERM_DB} WHERE user_id = %s AND expires_at > CURRENT_DATE",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row or not row[0]:
            return ""
        return "\n".join(row[0])
    except Exception as e:
        print(f"Error get_recent_conversation: {e}")
        return ""


def update_current_cache(user_id: str, cache_data: Dict[str, Any]) -> bool:
    """Merge cache_data into current_cache and extend expiry."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT recent_messages, current_cache, created_at FROM {SHORT_TERM_DB} WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            recent_messages = row[0] or []
            existing = (row[1] or {}) if row[1] else {}
            created_at = row[2]
        else:
            recent_messages = []
            existing = {}
            created_at = datetime.now().date()
        updated = {**existing, **cache_data}
        expires_at = (datetime.now() + timedelta(hours=EXPIRY_HOURS)).date()
        if row is not None:
            cursor.execute(
                f"UPDATE {SHORT_TERM_DB} SET current_cache = %s, expires_at = %s WHERE user_id = %s",
                (json.dumps(updated), expires_at, user_id),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {SHORT_TERM_DB} (user_id, recent_messages, current_cache, created_at, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, json.dumps(recent_messages), json.dumps(updated), created_at, expires_at),
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error update_current_cache: {e}")
        return False


def get_current_cache(user_id: str) -> Dict[str, Any]:
    """Return current_cache dict; empty if expired or missing."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT current_cache FROM {SHORT_TERM_DB} WHERE user_id = %s AND expires_at > CURRENT_DATE",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return (row[0] or {}) if row and row[0] else {}
    except Exception as e:
        print(f"Error get_current_cache: {e}")
        return {}


def cleanup_expired_entries() -> int:
    """Delete expired rows; return count deleted."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {SHORT_TERM_DB} WHERE expires_at < CURRENT_DATE")
        n = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return n
    except Exception as e:
        print(f"Error cleanup_expired_entries: {e}")
        return 0


def clear_user_data(user_id: str) -> bool:
    """Remove all short-term data for user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {SHORT_TERM_DB} WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clear_user_data: {e}")
        return False


def update_command_stack(user_id: str, command_stack: List[Dict]) -> bool:
    """Store command_stack in current_cache."""
    return update_current_cache(user_id, {"command_stack": command_stack})


def get_command_stack(user_id: str) -> List[Dict]:
    """Read command_stack from current_cache."""
    return get_current_cache(user_id).get("command_stack", [])
