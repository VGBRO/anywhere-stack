"""Canonical history — append-only event log for a project repo."""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def parse_json(raw: str) -> dict:
    """Extract and parse JSON from a model response. Handles code fences and bare JSON."""
    text = (raw or "").strip()
    # Try bare JSON first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Extract first {...} block — handles code fences even when content has backticks
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


def _runs_dir(repo_path: str) -> Path:
    path = Path(repo_path) / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_event(repo_path: str, event: dict) -> Path:
    """Append a structured event to the canonical history. Returns the event file path."""
    runs = _runs_dir(repo_path)
    ts = datetime.now(timezone.utc)
    filename = f"{ts.strftime('%Y%m%dT%H%M%SZ')}-{event.get('type', 'event')}.json"
    event_file = runs / filename
    event["timestamp"] = ts.isoformat()
    event_file.write_text(json.dumps(event, indent=2))
    return event_file


def read_recent_events(repo_path: str, n: int = 20) -> list[dict]:
    """Read the N most recent events from the canonical history."""
    runs = _runs_dir(repo_path)
    files = sorted(runs.glob("*.json"), reverse=True)[:n]
    events = []
    for f in reversed(files):
        try:
            events.append(json.loads(f.read_text()))
        except Exception:
            pass
    return events


def read_state(repo_path: str) -> str:
    """Read the machine-readable state projection."""
    state_file = Path(repo_path) / "state.md"
    return state_file.read_text() if state_file.exists() else ""


def read_brief(repo_path: str) -> str:
    """Read the human-readable brief projection."""
    brief_file = Path(repo_path) / "brief.md"
    return brief_file.read_text() if brief_file.exists() else ""


def read_agent_os(repo_path: str) -> str:
    """Read the project's agent-os.md — the entry point for any agent."""
    agent_os = Path(repo_path) / "agent-os.md"
    return agent_os.read_text() if agent_os.exists() else ""


def read_decisions(repo_path: str) -> str:
    """Read the decision log."""
    decisions = Path(repo_path) / "decisions.md"
    return decisions.read_text() if decisions.exists() else ""


def read_open_issues(repo_path: str) -> list[dict]:
    """Read open issues from the issues/ directory."""
    issues_dir = Path(repo_path) / "issues"
    if not issues_dir.exists():
        return []
    issues = []
    for f in sorted(issues_dir.glob("*.json")):
        try:
            issue = json.loads(f.read_text())
            if issue.get("status") not in ("done", "closed"):
                issues.append(issue)
        except Exception:
            pass
    return issues
