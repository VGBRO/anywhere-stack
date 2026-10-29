"""Projection generation — derives human/agent-readable views from canonical state."""

from datetime import datetime, timezone
from pathlib import Path
from anywhere.client import reason, Model


def generate_brief(repo_path: str, context: str) -> str:
    """Generate a fresh human-readable brief from canonical state context."""
    system = (
        "You generate a concise project brief from canonical state. "
        "Output clean markdown. Be factual and brief — this is read by humans and agents alike. "
        "Structure: current phase, last action, open issues, next action, health (green/yellow/red)."
    )
    prompt = f"Generate a brief.md for this project based on the following state:\n\n{context}"
    return reason(prompt, system=system, model=Model.NANO)


def write_brief(repo_path: str, content: str) -> None:
    brief_file = Path(repo_path) / "brief.md"
    ts = datetime.now(timezone.utc).isoformat()
    brief_file.write_text(f"_Generated: {ts}_\n\n{content}")


def generate_state(repo_path: str, context: str) -> str:
    """Generate a machine-readable state.md from canonical state context."""
    system = (
        "You generate a machine-readable state projection in YAML frontmatter + markdown. "
        "Include: phase, health, last_update, blocker, pending_approvals, next_action. "
        "Be precise and terse."
    )
    prompt = f"Generate state.md for this project:\n\n{context}"
    return reason(prompt, system=system, model=Model.NANO)


def write_state(repo_path: str, content: str) -> None:
    state_file = Path(repo_path) / "state.md"
    ts = datetime.now(timezone.utc).isoformat()
    state_file.write_text(f"_Generated: {ts}_\n\n{content}")
