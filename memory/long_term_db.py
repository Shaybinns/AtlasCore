"""
Long-term memory: user facts and recent command results for stateful agent.
Postgres-backed; use DATABASE_URL (e.g. Railway).
"""
import psycopg2
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
load_dotenv()

LONG_TERM_DB = "long_term_memory"
MAX_RECENT_RESULTS = 50


def get_db_connection():
    """Connection using Railway-injected DATABASE_URL."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def get_user_facts(user_id: str) -> str:
    """
    Return a single string of user context for the brain: facts + recent results.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT facts, recent_results FROM {LONG_TERM_DB} WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return "No long-term memory for this user."
        facts = (row[0] or "").strip()
        raw_results = row[1]
        if isinstance(raw_results, str):
            try:
                results = json.loads(raw_results)
            except Exception:
                results = []
        else:
            results = list(raw_results) if raw_results else []
        if not facts and not results:
            return "No long-term memory for this user."
        parts = []
        if facts:
            parts.append("=== USER CONTEXT ===\n" + facts)
        if results:
            parts.append("\n=== RECENT RESULTS ===")
            for i, r in enumerate((results[-10:] if len(results) > 10 else results), 1):
                if isinstance(r, dict):
                    cmd = r.get("command", "?")
                    summary = r.get("summary", r.get("result", str(r)))
                    parts.append(f"{i}. [{cmd}] {summary}")
                else:
                    parts.append(f"{i}. {r}")
        return "\n".join(parts)
    except Exception as e:
        print(f"Error get_user_facts: {e}")
        return "Error retrieving user facts."


def save_result(user_id: str, result: str, command_name: str = "command") -> bool:
    """
    Append a command result to long-term memory (recent_results).
    result: summary string; command_name: e.g. asset_assess.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT facts, recent_results, created_at FROM {LONG_TERM_DB} WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        now = datetime.utcnow()
        entry = {"command": command_name, "summary": result, "at": now.isoformat()}
        if row:
            facts = row[0] or ""
            raw = row[1]
            if isinstance(raw, str):
                try:
                    results = json.loads(raw)
                except Exception:
                    results = []
            else:
                results = list(raw) if raw else []
            created_at = row[2]
            results.append(entry)
            if len(results) > MAX_RECENT_RESULTS:
                results = results[-MAX_RECENT_RESULTS:]
            cursor.execute(
                f"UPDATE {LONG_TERM_DB} SET recent_results = %s, updated_at = %s WHERE user_id = %s",
                (json.dumps(results), now, user_id),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {LONG_TERM_DB} (user_id, facts, recent_results, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, "", json.dumps([entry]), now, now),
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error save_result: {e}")
        return False


def update_facts(user_id: str, facts: str) -> bool:
    """Set or replace the free-form facts text for the user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT user_id FROM {LONG_TERM_DB} WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        now = datetime.utcnow()
        if row:
            cursor.execute(
                f"UPDATE {LONG_TERM_DB} SET facts = %s, updated_at = %s WHERE user_id = %s",
                (facts, now, user_id),
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {LONG_TERM_DB} (user_id, facts, recent_results, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, facts, json.dumps([]), now, now),
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error update_facts: {e}")
        return False


def get_latest_result(command_name: str, symbol: str = None) -> Optional[Dict[str, Any]]:
    """Optional: return latest stored result for a command (e.g. for asset_assess)."""
    return None


def clear_user_data(user_id: str) -> bool:
    """Delete all long-term data for user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {LONG_TERM_DB} WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clear_user_data: {e}")
        return False
