"""Offline fallback — local intent capture without network.

When ANTHROPIC_API_KEY is unavailable or the network is down, this module
handles basic intent classification using a local Ollama model (optional).
If Ollama is not running, intents are queued and processed when Claude
comes back online.

Optional local setup:
    brew install ollama
    ollama pull llama3.2:1b   # ~1.3GB — fast on Apple Silicon
"""
import json
import subprocess
import requests

OFFLINE_MODEL = "llama3.2:1b"
OLLAMA_URL = "http://localhost:11434"


def is_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=1)
        if r.status_code != 200:
            return False
        models = [m["name"] for m in r.json().get("models", [])]
        return any(OFFLINE_MODEL.split(":")[0] in m for m in models)
    except Exception:
        return False


def classify_intent(text: str) -> dict:
    """Classify a user intent using the local model via Ollama."""
    prompt = f"""Classify this user intent into a JSON object with keys:
- project: the project name this relates to (or "unknown")
- action_type: one of [capture, query, task, update, unknown]
- summary: one sentence summary

User: {text}

Respond with only valid JSON."""

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OFFLINE_MODEL, "prompt": prompt, "stream": False},
            timeout=10,
        )
        raw = r.json().get("response", "")
        return json.loads(raw)
    except Exception:
        return {"project": "unknown", "action_type": "capture", "summary": text[:120]}
