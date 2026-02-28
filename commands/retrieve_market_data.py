"""
Retrieve market data from InvestCore's short_term_memory (INVESTCORE_DATABASE_URL).
Reads the row for user_id 00000000-0000-0000-0000-000000000000, gets current_market_data
and current_emerging_themes, then returns a contextual summary for trading and investments.
"""
import os
import json
import psycopg2
from dotenv import load_dotenv
from llm_model import call_gpt

load_dotenv()

INVESTCORE_USER_ID = "00000000-0000-0000-0000-000000000000"
TABLE = "short_term_memory"


def fetch_investcore_market_data():
    """
    Fetch current_market_data and current_emerging_themes from InvestCore short_term_memory
    for the system user. Returns (current_market_data, current_emerging_themes) or (None, None) on error.
    Shared by retrieve_market_data and daily_report.
    """
    url = os.getenv("INVESTCORE_DATABASE_URL")
    if not url:
        return None, None
    try:
        conn = psycopg2.connect(url)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT current_market_data, current_emerging_themes
                FROM short_term_memory
                WHERE user_id = %s
                """,
                (INVESTCORE_USER_ID,),
            )
        except psycopg2.ProgrammingError:
            cursor.execute(
                """
                SELECT current_cache
                FROM short_term_memory
                WHERE user_id = %s
                """,
                (INVESTCORE_USER_ID,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if not row or not row[0]:
                return None, None
            cache = row[0]
            a = cache.get("current_market_data") if isinstance(cache, dict) else None
            b = cache.get("current_emerging_themes") if isinstance(cache, dict) else None
            return a, b
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None, None
        return row[0], row[1]
    except Exception:
        return None, None


def run(args: dict):
    current_market_data, current_emerging_themes = fetch_investcore_market_data()
    if current_market_data is None and current_emerging_themes is None:
        return "[Error: INVESTCORE_DATABASE_URL not set or no data found]"
    return _summarize(current_market_data, current_emerging_themes)


def _summarize(current_market_data, current_emerging_themes):
    """Build a contextual summary for trading and investment implications."""
    if not current_market_data and not current_emerging_themes:
        return "No market data or emerging themes found in InvestCore for the system user."

    # psycopg2 JSONB returns dict/list; normalize for serialization
    def _norm(x):
        if x is None:
            return None
        if isinstance(x, (dict, list)):
            return x
        if isinstance(x, str):
            try:
                return json.loads(x)
            except Exception:
                return x
        return x

    raw = {
        "current_market_data": _norm(current_market_data),
        "current_emerging_themes": _norm(current_emerging_themes),
    }
    data_str = json.dumps(raw, default=str, indent=2)

    system = """You are a concise analyst. Given raw market data and emerging themes from InvestCore, produce a short, actionable summary. Focus on:
1. What the data implies for trading (short-term) and for investments (medium/long-term).
2. Key risks and opportunities.
3. One or two concrete implications. Be direct and avoid filler."""

    user_prompt = f"""Summarize the following InvestCore market data and emerging themes. State what this means for trading and for investments. Be contextual and relevant.

{data_str}"""

    try:
        summary = call_gpt(system, user_prompt, atlas_type="thinking")
        return summary.strip()
    except Exception as e:
        return f"Summary failed: {str(e)}\n\nRaw data available:\n{data_str[:2000]}"
