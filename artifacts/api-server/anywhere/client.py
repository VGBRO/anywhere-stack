"""Anthropic API client — Claude Haiku / Sonnet / Opus."""
import os
from anthropic import Anthropic
from enum import Enum

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class Model(str, Enum):
    OPUS   = "claude-opus-4-5"    # CoS heartbeat, complex reasoning
    SONNET = "claude-sonnet-4-5"  # PM triage, task planning
    HAIKU  = "claude-haiku-4-5"   # Fast routing, classification


def get_client() -> Anthropic:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def reason(messages: list[dict], model: Model = Model.SONNET, **kwargs) -> str:
    """Single completion via Anthropic. Returns assistant text."""
    client = get_client()
    response = client.messages.create(
        model=model.value,
        max_tokens=kwargs.pop("max_tokens", 2048),
        messages=messages,
        **kwargs,
    )
    return response.content[0].text
