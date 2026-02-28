"""
User tracking — registration, authentication, and chat message history.

Uses the `users` table:
  user_id         UUID PRIMARY KEY (auto-generated)
  email           VARCHAR(255) UNIQUE NOT NULL
  password        VARCHAR(255)        — bcrypt hash, nullable for future OAuth
  full_name       VARCHAR(255)
  created_at      TIMESTAMPTZ         DEFAULT CURRENT_TIMESTAMP
  recent_messages JSONB               DEFAULT '[]'

recent_messages: list of {"role": "user"|"assistant", "content": "...", "ts": "ISO"}.
Trimmed to MAX_RECENT_MESSAGES on every write.
"""

import uuid
import json
import bcrypt
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from database import get_db_connection

MAX_RECENT_MESSAGES = 20


# =============================================================================
# USER MANAGEMENT
# =============================================================================

def create_user(email: str, password: str, full_name: str) -> Optional[Dict[str, Any]]:
    """
    Register a new user.
    Hashes password with bcrypt. Returns created user dict (no password) or None.
    Raises ValueError if email is already registered.
    """
    email = email.strip().lower()
    if get_user_by_email(email):
        raise ValueError(f"Email already registered: {email}")

    user_id = str(uuid.uuid4())
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    created_at = datetime.now(timezone.utc)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, email, password, full_name, created_at, recent_messages)
            VALUES (%s::uuid, %s, %s, %s, %s, %s)
        """, (user_id, email, hashed_pw, full_name, created_at, json.dumps([])))
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "created_at": created_at.isoformat(),
        }
    except Exception as e:
        print(f"[users] create_user error: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Return full user row (including hashed password) or None."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, email, password, full_name, created_at
            FROM users WHERE email = %s
        """, (email.strip().lower(),))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return {
            "user_id": str(row[0]),
            "email": row[1],
            "password": row[2],
            "full_name": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
        }
    except Exception as e:
        print(f"[users] get_user_by_email error: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Return user row (without password) or None."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, email, full_name, created_at
            FROM users WHERE user_id = %s::uuid
        """, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return {
            "user_id": str(row[0]),
            "email": row[1],
            "full_name": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
        }
    except Exception as e:
        print(f"[users] get_user_by_id error: {e}")
        return None


def is_user_active(user_id: str) -> bool:
    """True if the user exists."""
    return get_user_by_id(user_id) is not None


def verify_password(plain: str, hashed: str) -> bool:
    """Check plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        print(f"[users] verify_password error: {e}")
        return False


# =============================================================================
# MESSAGE HISTORY (users.recent_messages JSONB)
# =============================================================================

def add_message(user_id: str, role: str, content: str) -> bool:
    """
    Append a message to the user's recent_messages.
    role must be "user" or "assistant". Trims to MAX_RECENT_MESSAGES.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT recent_messages FROM users WHERE user_id = %s::uuid",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return False

        messages = list(row[0]) if row[0] else []
        messages.append({
            "role": role,
            "content": content,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        if len(messages) > MAX_RECENT_MESSAGES:
            messages = messages[-MAX_RECENT_MESSAGES:]

        cursor.execute(
            "UPDATE users SET recent_messages = %s WHERE user_id = %s::uuid",
            (json.dumps(messages), user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[users] add_message error: {e}")
        return False


def get_messages(user_id: str) -> List[Dict[str, Any]]:
    """Return recent messages for a user (oldest first)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT recent_messages FROM users WHERE user_id = %s::uuid",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row or not row[0]:
            return []
        return row[0]
    except Exception as e:
        print(f"[users] get_messages error: {e}")
        return []


def clear_messages(user_id: str) -> bool:
    """Clear message history for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET recent_messages = %s WHERE user_id = %s::uuid",
            (json.dumps([]), user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[users] clear_messages error: {e}")
        return False
