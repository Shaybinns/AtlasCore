"""
Data collection state: persisted in short_term current_cache so the agent stays stateful across restarts.
"""
from memory.short_term_cache import get_current_cache, update_current_cache
from utils.field_extraction import extract_fields_from_text

DATA_COLLECTION_KEY = "data_collection"


def needs_more_input(user_id: str) -> bool:
    """True if this user has an active data-collection session in cache."""
    cache = get_current_cache(user_id)
    entry = cache.get(DATA_COLLECTION_KEY)
    return entry is not None and isinstance(entry, dict) and entry.get("missing")


def start_data_collection(user_id: str, command_name: str, args: dict, missing_fields: list, required_fields: dict):
    """Start collecting missing fields; store in short_term cache."""
    # required_fields may be dict or list; ensure JSON-serializable
    if isinstance(required_fields, dict):
        field_meta = {k: v if isinstance(v, (str, int, float, bool, type(None))) else str(v) for k, v in required_fields.items()}
    else:
        field_meta = list(required_fields) if required_fields else []
    update_current_cache(user_id, {
        DATA_COLLECTION_KEY: {
            "command": command_name,
            "args": dict(args),
            "missing": list(missing_fields),
            "field_meta": field_meta,
        }
    })


def receive_input(user_id: str, user_message: str):
    """
    Process user message against current data collection.
    Returns the filled command dict when all missing fields are filled; otherwise None.
    """
    cache = get_current_cache(user_id)
    entry = cache.get(DATA_COLLECTION_KEY)
    if not entry or not isinstance(entry, dict) or not entry.get("missing"):
        return None

    args = dict(entry["args"])
    required_fields = entry.get("field_meta") or {}
    missing = list(entry["missing"])

    extracted = extract_fields_from_text(user_message, required_fields)
    for key, value in extracted.items():
        if key in missing:
            args[key] = value
            missing.remove(key)

    if not missing:
        # All filled: clear data_collection and return the command payload
        update_current_cache(user_id, {DATA_COLLECTION_KEY: None})
        return {"command": entry["command"], "args": args, "missing": [], "field_meta": required_fields}

    # Still missing: update cache with new args/missing
    update_current_cache(user_id, {
        DATA_COLLECTION_KEY: {
            "command": entry["command"],
            "args": args,
            "missing": missing,
            "field_meta": required_fields,
        }
    })
    return None
