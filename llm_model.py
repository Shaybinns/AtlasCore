from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Atlas type -> OpenRouter model id
ATLAS_MODELS = {
    "normal": "openai/gpt-5-nano",
    "coding": "anthropic/claude-sonnet-4.6",
    "thinking": "openai/gpt-5.2",
    "internet": "perplexity/sonar-pro",
    "experiment": "switchpoint/router",
}

# Default when not using OpenRouter (e.g. missing key)
DEFAULT_MODEL = "gpt-4o-mini"

_openai_client = None
_openrouter_client = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _get_openrouter_client():
    # Returns OpenAI client configured for OpenRouter, or None if no key
    global _openrouter_client
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return None
    if _openrouter_client is None:
        _openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )
    return _openrouter_client


def call_gpt(system_prompt: str, user_prompt: str, atlas_type: str = "normal") -> str:
    """
    Call the LLM. Uses OpenRouter when OPENROUTER_API_KEY is set and atlas_type
    is one of the Atlas types; otherwise falls back to OpenAI with default model.
    """
    client = _get_openrouter_client()
    model = ATLAS_MODELS.get(atlas_type, ATLAS_MODELS["normal"])

    if client is not None:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1000,
            temperature=0.5,
        )
        return response.choices[0].message.content

    # Fallback: OpenAI with default model
    response = _get_openai_client().chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
        temperature=0.5,
    )
    return response.choices[0].message.content
