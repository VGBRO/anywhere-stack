"""Nebius Token Factory client — OpenAI-compatible, powered by NVIDIA Nemotron."""

from __future__ import annotations

import json
import os
from enum import Enum
from typing import Callable, Optional
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
    # Tool calling + hybrid reasoning — agentic loops, Builder tasks
    HERMES = "NousResearch/Hermes-4-405B"
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
    return response.choices[0].message.content or ""


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


def execute_with_tools(
    prompt: str,
    tools: list[dict] | None = None,
    executor: Callable[[str, dict], str] | None = None,
    system: str = "",
    model: Model = Model.HERMES,
    max_iterations: int = 10,
) -> str:
    """
    Multi-turn agentic loop: model reasons, calls tools, observes results, repeats.

    tools:    OpenAI-format schemas — [{"type": "function", "function": {"name": ..., "parameters": ...}}]
    executor: callable(tool_name: str, args: dict) -> str  — routes tool calls to implementations
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    client = get_client()
    call_kwargs: dict = {"model": model.value, "temperature": 0.2, "max_tokens": 4096}
    if tools:
        call_kwargs["tools"] = tools

    for i in range(max_iterations):
        # First iteration: require a tool call so the model can't skip straight to text
        if tools:
            call_kwargs["tool_choice"] = "required" if i == 0 else "auto"
        response = client.chat.completions.create(messages=messages, **call_kwargs)
        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            return msg.content or ""

        # Append assistant turn with its tool call requests
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        # Execute each tool call and feed results back
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            if executor:
                try:
                    result = str(executor(tc.function.name, args))
                except Exception as e:
                    result = f"Tool error: {e}"
            else:
                result = f"Tool '{tc.function.name}' called with {args} — no executor configured."
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    # Max iterations reached — return the last assistant content we have
    for m in reversed(messages):
        if m.get("role") == "assistant" and m.get("content"):
            return m["content"]
    return "Max iterations reached without a final answer."
