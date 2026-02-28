"""
Daily report: market data (InvestCore), web headlines, events today (placeholder), weather (placeholder).
Uses the same InvestCore fetch as retrieve_market_data (no summary); runs search_web for headlines;
placeholders for calendar and weather until plugins are added.
"""
import json
from datetime import datetime
from commands.retrieve_market_data import fetch_investcore_market_data
from llm_model import call_gpt


# -----------------------------------------------------------------------------
# Placeholders (replace when calendar/weather plugins are added)
# -----------------------------------------------------------------------------

def get_events_today(user_id: str):
    """Placeholder: calendar plugin not yet connected."""
    return "[Calendar plugin not yet connected. Your events for today will appear here.]"


def get_weather_today(location: str = None):
    """Placeholder: weather plugin not yet connected."""
    if not location:
        return "[Weather plugin not yet connected. Set your location (e.g. in preferences) to see today's weather.]"
    return f"[Weather plugin not yet connected. When added, weather for '{location}' will appear here.]"


# -----------------------------------------------------------------------------
# Report builder
# -----------------------------------------------------------------------------

def run(args: dict):
    user_id = args.get("user_id", "")
    location = (args.get("location") or "").strip() or None

    sections = []
    today = datetime.now().strftime("%A, %B %d, %Y")

    # 1. Market data from InvestCore (raw, no summary)
    current_market_data, current_emerging_themes = fetch_investcore_market_data()
    if current_market_data or current_emerging_themes:
        raw = {
            "current_market_data": _norm_json(current_market_data),
            "current_emerging_themes": _norm_json(current_emerging_themes),
        }
        sections.append(f"## Market data (InvestCore)\n{json.dumps(raw, default=str, indent=2)[:4000]}")
    else:
        sections.append("## Market data (InvestCore)\nNo InvestCore data available (check INVESTCORE_DATABASE_URL or system user row).")

    # 2. Web search: current headlines across domains
    headlines_query = (
        "Today's top headlines and notable news worldwide: finance, markets, world news, "
        "politics, technology, culture. What is currently going on and what is notable today?"
    )
    try:
        from commands.search_web import run as run_search_web
        search_result = run_search_web({"query": headlines_query})
        sections.append(f"## Headlines & what's going on\n{search_result}")
    except Exception as e:
        sections.append(f"## Headlines & what's going on\n[Search failed: {e}]")

    # 3. Events today (placeholder)
    sections.append(f"## Your events today\n{get_events_today(user_id)}")

    # 4. Weather (placeholder)
    sections.append(f"## Weather today\n{get_weather_today(location)}")

    # Single narrative report
    report_raw = "\n\n".join(sections)
    system = (
        "You are a concise daily brief writer. Given raw sections (market data, headlines, events placeholder, weather placeholder), "
        "produce a short, readable daily report. Structure: brief intro, then market/InvestCore snapshot, then what's going on in the world, "
        "then events and weather (clearly note if those are placeholders). Be direct and scannable."
    )
    user_prompt = f"Write today's daily report ({today}) from the following gathered sections.\n\n{report_raw}"

    try:
        return call_gpt(system, user_prompt, atlas_type="normal")
    except Exception as e:
        return f"Report synthesis failed: {e}\n\n---\nRaw sections:\n{report_raw}"


def _norm_json(x):
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
