"""Nebius Token Factory client — OpenAI-compatible, powered by NVIDIA Nemotron."""

import os
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")


class Model(str, Enum):
    # Deep reasoning — Chief of Staff heartbeat, complex analysis
    ULTRA = "nvidia/Nemotron-3-Ultra-550b-a55b"
    # Balanced — Project Manager reasoning, task planning
    SUPER = "nvidia/nemotron-3-super-120b-a12b"
    # Fast — routing, triage, simple decisions
    NANO = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
    # Fastest — high-frequency calls, formatting, extraction
    LIGHTNING = "nvidia/Nemotron-3_5-Lightning"


def get_client() -> OpenAI:
    if not NEBIUS_API_KEY:
        raise RuntimeError("NEBIUS_API_KEY not set. Copy .env.example to .env and add your key.")
    return OpenAI(base_url=NEBIUS_BASE_URL, api_key=NEBIUS_API_KEY)


def complete(
    messages: list[dict],
    model: Model = Model.SUPER,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=model.value,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def reason(prompt: str, system: str = "", model: Model = Model.ULTRA) -> str:
    """Single-turn reasoning call — use for CoS heartbeat and complex decisions."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return complete(messages, model=model, temperature=0.2, max_tokens=4096)


def route(prompt: str, system: str = "", model: Model = Model.NANO) -> str:
    """Fast routing call — use for triage, classification, quick decisions."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return complete(messages, model=model, temperature=0.1, max_tokens=512)
