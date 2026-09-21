"""Heartbeat engine — wake, inspect, act, record, exit."""

import json
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from anywhere.client import reason, route, Model
from anywhere.state.canonical import (
    append_event,
    parse_json,
    read_agent_os,
    read_brief,
    read_decisions,
    read_open_issues,
    read_recent_events,
    read_state,
)
from anywhere.state.projection import generate_brief, generate_state, write_brief, write_state

console = Console()


class HeartbeatResult:
    def __init__(self, role: str, repo_path: str):
        self.role = role
        self.repo_path = repo_path
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.observations: list[str] = []
        self.actions_taken: list[str] = []
        self.decisions: list[str] = []
        self.escalations: list[str] = []
        self.next_actions: list[str] = []
        self.health: str = "green"

    def to_dict(self) -> dict:
        return {
            "type": "heartbeat",
            "role": self.role,
            "repo": self.repo_path,
            "timestamp": self.timestamp,
            "observations": self.observations,
            "actions_taken": self.actions_taken,
            "decisions": self.decisions,
            "escalations": self.escalations,
            "next_actions": self.next_actions,
            "health": self.health,
        }


def _load_project_context(repo_path: str) -> str:
    """Assemble the full readable context for a project repo."""
    parts = []
    agent_os = read_agent_os(repo_path)
    if agent_os:
        parts.append(f"## agent-os.md\n{agent_os}")
    state = read_state(repo_path)
    if state:
        parts.append(f"## state.md\n{state}")
    brief = read_brief(repo_path)
    if brief:
        parts.append(f"## brief.md\n{brief}")
    decisions = read_decisions(repo_path)
    if decisions:
        parts.append(f"## decisions.md\n{decisions}")
    issues = read_open_issues(repo_path)
    if issues:
        parts.append(f"## Open Issues\n{json.dumps(issues, indent=2)}")
    recent = read_recent_events(repo_path, n=10)
    if recent:
        parts.append(f"## Recent Events (last 10)\n{json.dumps(recent, indent=2)}")
    return "\n\n---\n\n".join(parts) if parts else "(empty project — no state files found)"


def run_project_heartbeat(repo_path: str, role: str = "project_manager") -> HeartbeatResult:
    """
    Run one bounded heartbeat for a project repo.
    Wake → Inspect → Act → Record → Exit
    """
    result = HeartbeatResult(role=role, repo_path=repo_path)
    project_name = Path(repo_path).name

    console.print(f"\n[bold blue]► Heartbeat[/bold blue] {role} @ {project_name}")

    # 1. INSPECT — load canonical state
    console.print("  [dim]Inspecting state...[/dim]")
    context = _load_project_context(repo_path)

    skill_path = Path(__file__).parent.parent / "skills" / f"{role.replace('_', '-')}-skill.md"
    role_skill = skill_path.read_text() if skill_path.exists() else ""

    contracts_path = Path(__file__).parent.parent / "contracts" / f"{role.replace('_', '-')}.md"
    role_contract = contracts_path.read_text() if contracts_path.exists() else ""

    # 2. ACT — reason about current state and determine actions
    system = f"""You are running a bounded {role} heartbeat. Your job is to:
1. Inspect the current project state
2. Identify what requires attention (blockers, stale work, pending approvals)
3. Determine the single highest-priority next action
4. Record any decisions made
5. Flag anything requiring human escalation

{f"Role skill:{chr(10)}{role_skill}" if role_skill else ""}
{f"Role contract:{chr(10)}{role_contract}" if role_contract else ""}

Respond in JSON with this exact structure:
{{
  "observations": ["observation 1", "observation 2"],
  "actions_taken": ["action 1"],
  "decisions": ["decision 1"],
  "escalations": ["escalation 1"],
  "next_actions": ["next action 1"],
  "health": "green|yellow|red",
  "summary": "one sentence summary of this heartbeat"
}}"""

    prompt = f"Run a heartbeat for this project. Current state:\n\n{context}"

    console.print("  [dim]Reasoning with Nemotron...[/dim]")
    model = Model.ULTRA if role == "cos" else Model.SUPER
    raw = reason(prompt, system=system, model=model)

    # Parse response
    parsed = parse_json(raw)
    if parsed:
        result.observations = parsed.get("observations", [])
        result.actions_taken = parsed.get("actions_taken", [])
        result.decisions = parsed.get("decisions", [])
        result.escalations = parsed.get("escalations", [])
        result.next_actions = parsed.get("next_actions", [])
        result.health = parsed.get("health", "green")
        summary = parsed.get("summary", "Heartbeat completed.")
    else:
        result.observations = [(raw or "")[:500]]
        summary = "Heartbeat completed (unparsed response)."

    # 3. RECORD — append to canonical history
    event = result.to_dict()
    event["summary"] = summary
    event_file = append_event(repo_path, event)

    # 4. Regenerate projections
    console.print("  [dim]Regenerating projections...[/dim]")
    fresh_context = _load_project_context(repo_path)
    brief_content = generate_brief(repo_path, fresh_context)
    state_content = generate_state(repo_path, fresh_context)
    write_brief(repo_path, brief_content)
    write_state(repo_path, state_content)

    # 5. EXIT — print summary
    health_color = {"green": "green", "yellow": "yellow", "red": "red"}.get(result.health, "white")
    console.print(f"  [{health_color}]● {result.health.upper()}[/{health_color}] {summary}")
    if result.escalations:
        console.print(f"  [bold red]⚠ Escalations:[/bold red]")
        for e in result.escalations:
            console.print(f"    • {e}")

    return result
