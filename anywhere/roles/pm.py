"""Project Manager role — project-level state reconciliation and task delegation."""

import json
from pathlib import Path
from anywhere.client import reason, Model
from anywhere.state.canonical import (
    append_event,
    read_agent_os,
    read_open_issues,
    read_recent_events,
    read_state,
)


def create_issue(repo_path: str, title: str, description: str, priority: str = "medium") -> dict:
    """Create a new issue in the project's issues/ directory."""
    issues_dir = Path(repo_path) / "issues"
    issues_dir.mkdir(exist_ok=True)
    existing = list(issues_dir.glob("*.json"))
    issue_id = f"{len(existing) + 1:04d}"
    issue = {
        "id": issue_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "open",
        "assigned_to": None,
        "created_at": None,
    }
    from datetime import datetime, timezone
    issue["created_at"] = datetime.now(timezone.utc).isoformat()
    issue_file = issues_dir / f"{issue_id}-{title[:40].lower().replace(' ', '-')}.json"
    issue_file.write_text(json.dumps(issue, indent=2))
    return issue


def close_issue(repo_path: str, issue_id: str, resolution: str) -> bool:
    """Mark an issue as done."""
    issues_dir = Path(repo_path) / "issues"
    for f in issues_dir.glob(f"{issue_id}*.json"):
        issue = json.loads(f.read_text())
        issue["status"] = "done"
        issue["resolution"] = resolution
        f.write_text(json.dumps(issue, indent=2))
        return True
    return False


def run_pm_triage(repo_path: str) -> dict:
    """
    Project Manager triage — inspect state, prioritize open issues,
    determine next action, record result.
    """
    agent_os = read_agent_os(repo_path)
    state = read_state(repo_path)
    issues = read_open_issues(repo_path)
    recent = read_recent_events(repo_path, n=5)

    context = f"""Project: {Path(repo_path).name}

## agent-os.md
{agent_os}

## Current State
{state}

## Open Issues ({len(issues)})
{json.dumps(issues, indent=2)}

## Recent Events
{json.dumps(recent, indent=2)}"""

    skill_path = Path(__file__).parent.parent.parent / "skills" / "pm-skill.md"
    role_skill = skill_path.read_text() if skill_path.exists() else ""

    system = f"""You are a Project Manager running a triage heartbeat.
Inspect the project state, prioritize open issues, and determine the single most important next action.

{f"Role skill:{chr(10)}{role_skill}" if role_skill else ""}

Respond in JSON:
{{
  "priority_issue": {{"id": "...", "title": "...", "reason": "why this is highest priority"}},
  "blockers": ["blocker 1"],
  "recommended_action": "one clear next action",
  "health": "green|yellow|red",
  "notes": "any other observations"
}}"""

    raw = reason(context, system=system, model=Model.SUPER)

    try:
        raw_clean = raw.strip()
        if "```" in raw_clean:
            raw_clean = raw_clean.split("```")[1]
            if raw_clean.startswith("json"):
                raw_clean = raw_clean[4:]
        result = json.loads(raw_clean.strip())
    except Exception:
        result = {"recommended_action": raw[:200], "health": "yellow", "blockers": []}

    append_event(repo_path, {
        "type": "pm_triage",
        "result": result,
    })

    return result
