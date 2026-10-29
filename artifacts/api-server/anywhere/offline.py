"""Offline local model — Ollama + Nemotron Mini for on-device intent capture.

This module powers Anywhere Stack when there is no internet connection.
It runs a small Nemotron model locally via Ollama for basic intent
classification and queuing — no cloud calls, no data leaving the device.

Setup:
    brew install ollama
    ollama serve &
    ollama pull nemotron-mini

Usage:
    from anywhere.offline import classify_intent_offline
    result = classify_intent_offline("I want to build an ADU in my backyard", projects)
"""

from __future__ import annotations

import json
from typing import Optional

import httpx

OLLAMA_BASE_URL = "http://localhost:11434"
OFFLINE_MODEL = "nemotron-mini"   # ~4GB — fast on Apple Silicon
FALLBACK_MODEL = "llama3.2:1b"    # ~1.3GB — smallest viable fallback


def _ollama_available() -> bool:
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def _which_model() -> Optional[str]:
    """Return the best available offline model, or None if Ollama is not running."""
    if not _ollama_available():
        return None
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        models = {m["name"].split(":")[0] for m in r.json().get("models", [])}
        if "nemotron-mini" in models:
            return OFFLINE_MODEL
        if "llama3.2" in models:
            return FALLBACK_MODEL
        return None
    except Exception:
        return None


def _ollama_generate(prompt: str, model: str, system: str = "") -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 256},
    }
    r = httpx.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=30.0)
    r.raise_for_status()
    return r.json().get("response", "")


OFFLINE_ROUTER_SYSTEM = """You are a fast intent router running locally on the user's device.
The device is OFFLINE. Your job is to classify the user's intent and match it to a project.
Respond ONLY with valid JSON: {"project_id": "<id or 'new'>", "project_name": "<name>", "is_new": <true|false>}"""


def classify_intent_offline(text: str, projects: list[dict]) -> dict:
    """
    Classify a user intent using the local Nemotron Mini model via Ollama.
    Falls back to keyword matching if Ollama is not available.

    This runs fully on-device — no network calls, no data leaves the machine.
    Results are queued for full CoS processing when connectivity is restored.
    """
    model = _which_model()

    if model:
        project_list = json.dumps([
            {"id": p.get("id"), "name": p.get("name"), "tags": p.get("tags", [])}
            for p in projects
        ])
        prompt = f"User intent: {text}\n\nProjects:\n{project_list}\n\nRoute this intent."
        try:
            raw = _ollama_generate(prompt, model=model, system=OFFLINE_ROUTER_SYSTEM)
            result = json.loads(raw.strip().strip("```json").strip("```").strip())
            result["offline"] = True
            result["model"] = model
            return result
        except Exception:
            pass

    # Keyword fallback — no Ollama required
    text_lower = text.lower()
    for p in projects:
        tags = [t.lower() for t in p.get("tags", [])]
        name = p.get("name", "").lower()
        if any(tag in text_lower for tag in tags) or name in text_lower:
            return {
                "project_id": p["id"],
                "project_name": p["name"],
                "is_new": False,
                "offline": True,
                "model": "keyword-fallback",
            }

    return {
        "project_id": "new",
        "project_name": "New Project",
        "is_new": True,
        "offline": True,
        "model": "keyword-fallback",
    }
