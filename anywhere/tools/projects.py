"""Project tools — issues, events, and state within a canonical repo."""

import json
from datetime import datetime, timezone
from pathlib import Path
from anywhere.state.canonical import read_open_issues, append_event as _append_event


def list_issues(repo_path: str) -> str:
    issues = read_open_issues(repo_path)
    if not issues:
        return "No open issues."
    return json.dumps(issues, indent=2)


def read_issue(repo_path: str, issue_id: str) -> str:
    issues_dir = Path(repo_path) / "issues"
    if not issues_dir.exists():
        return "No issues directory found."
    for f in issues_dir.glob(f"{issue_id}*.json"):
        return f.read_text()
    return f"Issue {issue_id} not found."


def create_issue(repo_path: str, title: str, description: str, priority: str = "medium") -> str:
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    slug = title[:40].lower().replace(" ", "-")
    (issues_dir / f"{issue_id}-{slug}.json").write_text(json.dumps(issue, indent=2))
    return f"Created issue {issue_id}: {title}"


def close_issue(repo_path: str, issue_id: str, resolution: str) -> str:
    issues_dir = Path(repo_path) / "issues"
    for f in issues_dir.glob(f"{issue_id}*.json"):
        issue = json.loads(f.read_text())
        issue["status"] = "done"
        issue["resolution"] = resolution
        f.write_text(json.dumps(issue, indent=2))
        return f"Issue {issue_id} closed."
    return f"Issue {issue_id} not found."


def record_event(repo_path: str, event_type: str, data: dict) -> str:
    _append_event(repo_path, {"type": event_type, **data})
    return f"Event '{event_type}' recorded."
