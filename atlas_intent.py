"""
Atlas intent detection: map user message to one of 5 Atlas types for model selection.
- normal: quick messages (default)
- coding: code, write, codify
- thinking: analyse, think, brainstorm
- internet: search, web, data
- experiment: multiple intents (use router when no single fit)
"""

from typing import Set

# Trigger words per Atlas type (lowercase). Overlap handled by "first category wins" per message.
THINKING_TRIGGERS: Set[str] = {"analyse", "analyze", "think", "brainstorm"}
CODING_TRIGGERS: Set[str] = {"code", "write", "codify"}
INTERNET_TRIGGERS: Set[str] = {"search", "web", "data"}


def detect_atlas_intent(message: str) -> str:
    """
    Detect which Atlas type best fits the user message.
    Returns one of: "normal", "coding", "thinking", "internet", "experiment".
    - No trigger word -> normal
    - Exactly one category triggered -> that type
    - Two or more categories triggered -> experiment (nuanced, use router)
    """
    if not message or not message.strip():
        return "normal"

    lower = message.lower()
    # Tokenize: split on non-alphanumeric to catch "think deeply" and "search the web"
    words = set()
    for word in lower.replace("-", " ").split():
        w = "".join(c for c in word if c.isalnum())
        if w:
            words.add(w)

    matched: Set[str] = set()
    if words & THINKING_TRIGGERS:
        matched.add("thinking")
    if words & CODING_TRIGGERS:
        matched.add("coding")
    if words & INTERNET_TRIGGERS:
        matched.add("internet")

    if len(matched) > 1:
        return "experiment"
    if "thinking" in matched:
        return "thinking"
    if "coding" in matched:
        return "coding"
    if "internet" in matched:
        return "internet"
    return "normal"
