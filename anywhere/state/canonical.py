"""Canonical history — append-only event log for a project repo."""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── ActiveGraph lineage (lazy, per-portfolio, best-effort) ───────────────────
_AG_STATE: dict[str, dict] = {}  # {portfolio_root: {graph, runtime}}


def _get_lineage_graph(portfolio_root: str) -> Optional[Any]:
    """Return the ActiveGraph Graph for this portfolio, creating it on first use."""
    if portfolio_root in _AG_STATE:
        return _AG_STATE[portfolio_root]["graph"]
    try:
        from activegraph import Graph, Runtime  # type: ignore
        db_path = str(Path(portfolio_root) / ".lineage.sqlite")
        graph = Graph()
        rt = Runtime(graph, persist_to=db_path)
        _AG_STATE[portfolio_root] = {"graph": graph, "runtime": rt}
        return graph
    except Exception:
        return None


def _mirror_to_graph(ag: Any, event: dict, project: str) -> None:
    """Write one event to the ActiveGraph lineage store."""
    try:
        flat: dict[str, Any] = {"project": project}
        for k, v in event.items():
            if isinstance(v, (str, int, float, bool)):
                flat[k] = v
        ag.add_object(event.get("type", "event"), data=flat)
    except Exception:
        pass  # lineage is always best-effort


# ── Core state operations ────────────────────────────────────────────────────

def parse_json(raw: str) -> dict:
    """Extract and parse JSON from a model response. Handles code fences and bare JSON."""
    text = (raw or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
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
    """Append a structured event to the canonical history and mirror to ActiveGraph."""
    runs = _runs_dir(repo_path)
    ts = datetime.now(timezone.utc)
    filename = f"{ts.strftime('%Y%m%dT%H%M%SZ')}-{event.get('type', 'event')}.json"
    event_file = runs / filename
    event["timestamp"] = ts.isoformat()
    event_file.write_text(json.dumps(event, indent=2))

    # Mirror to ActiveGraph (non-blocking — failure never surfaces to caller)
    try:
        portfolio_root = str(Path(repo_path).parent)
        ag = _get_lineage_graph(portfolio_root)
        if ag is not None:
            _mirror_to_graph(ag, event, Path(repo_path).name)
    except Exception:
        pass

    return event_file


def query_lineage(portfolio_root: str, event_type: Optional[str] = None,
                  project: Optional[str] = None) -> list[dict]:
    """
    Query the ActiveGraph lineage store for events.

    Returns a list of object data dicts. Useful for cross-project audit:
      query_lineage('projects', event_type='task_execution')
      query_lineage('projects', project='test-chain')
    """
    try:
        ag = _get_lineage_graph(portfolio_root)
        if ag is None:
            return []
        where: dict[str, Any] = {}
        if project:
            where["project"] = project
        objs = ag.objects(type=event_type, where=where if where else None)
        return [o.data for o in objs]
    except Exception:
        return []


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


def read_regime_proposals(repo_path: str, limit: int = 5) -> str:
    """Return a markdown summary of the most recent open regime.patch_proposed events.

    Included in heartbeat context so the LLM reasoning step sees pending proposals.
    Returns empty string if none.
    """
    recent = read_recent_events(repo_path, n=200)
    proposals = [
        e for e in recent
        if e.get("type") == "regime.patch_proposed" and e.get("status") == "proposed"
    ][-limit:]

    if not proposals:
        return ""

    lines = ["## Regime Proposals (pending review)"]
    for p in proposals:
        fix = p.get("fix", {})
        lines.append(
            f"- ({p.get('occurrences', '?')}×) `{p.get('pattern', '')[:60]}`"
        )
        lines.append(
            f"  Fix [{fix.get('confidence', '?')}]: {fix.get('fix_description', '')[:80]}"
        )
        lines.append(
            f"  Component: `{fix.get('affected_component', 'unknown')}`  "
            f"Test: {fix.get('test_criterion', 'n/a')[:60]}"
        )
    return "\n".join(lines)


def read_teamwork_graph(repo_path: str) -> str:
    """Read the teamwork graph SQLite and return a markdown summary for LLM context.

    Queries the event log directly (no Graph/Runtime replay) — fast and always safe.
    Returns empty string if no graph exists or on any error.

    The summary is appended to _load_project_context so generate_state / generate_brief
    automatically incorporate live teamwork entities into the projected state.md and brief.md.
    """
    import sqlite3 as _sqlite3

    db_path = Path(repo_path) / ".teamwork.sqlite"
    if not db_path.exists():
        return ""

    try:
        conn = _sqlite3.connect(str(db_path))

        # Reconstruct current object state from event log:
        #   1. Pull all object.created for relevant types
        #   2. Apply patch.applied updates on top
        _TYPES = ("task", "outcome", "decision", "blocker", "person")

        objects: dict[str, dict] = {}  # {id: data}
        obj_types: dict[str, str] = {}  # {id: type}

        rows = conn.execute(
            "SELECT payload FROM events WHERE type = 'object.created' ORDER BY id"
        ).fetchall()
        for (payload_json,) in rows:
            p = json.loads(payload_json) if payload_json else {}
            obj = p.get("object", {})
            obj_type = obj.get("type", "")
            obj_id = obj.get("id", "")
            if obj_type in _TYPES and obj_id:
                objects[obj_id] = dict(obj.get("data", {}))
                obj_types[obj_id] = obj_type

        patches = conn.execute(
            "SELECT payload FROM events WHERE type = 'patch.applied' ORDER BY id"
        ).fetchall()
        for (payload_json,) in patches:
            p = json.loads(payload_json) if payload_json else {}
            patch = p.get("patch", {})
            target = patch.get("target", "")
            if target in objects:
                objects[target].update(patch.get("value", {}))

        conn.close()

        # Build typed buckets
        def _collect(t: str) -> list[dict]:
            return [objects[oid] for oid, ot in obj_types.items() if ot == t]

        all_tasks     = _collect("task")
        all_outcomes  = _collect("outcome")
        all_decisions = _collect("decision")
        all_blockers  = _collect("blocker")

        open_tasks    = [t for t in all_tasks if t.get("status") == "open"]
        done_tasks    = [t for t in all_tasks if t.get("status") == "done"]
        open_blockers = [b for b in all_blockers if b.get("status") == "open"]

        sections: list[str] = []

        if all_tasks:
            lines = ["### Tasks"]
            for t in open_tasks:
                owner = t.get("owner", "")
                src = "github" if "github.com" in t.get("source", "") else "slack"
                conf = t.get("confidence", "")
                label = f"[{src}][{conf}] " if conf else f"[{src}] "
                lines.append(f"- [ ] {label}{t.get('title', '')}  — {owner}")
            for t in done_tasks:
                lines.append(f"- [x] {t.get('title', '')}")
            sections.append("\n".join(lines))

        if all_outcomes:
            lines = ["### Outcomes (delivered)"]
            for o in all_outcomes:
                date = (o.get("merged_at") or "")[:10]
                tag = f"  [{date}]" if date else ""
                lines.append(f"- {o.get('result', '')}{tag}")
            sections.append("\n".join(lines))

        if all_decisions:
            lines = ["### Decisions"]
            for d in all_decisions:
                state = d.get("epistemic_state", "")
                lines.append(f"- [{state}] {d.get('title', '')}")
            sections.append("\n".join(lines))

        if open_blockers:
            lines = ["### Blockers"]
            for b in open_blockers:
                severity = b.get("severity", "")
                lines.append(f"- [{severity}] {b.get('description', '')}")
            sections.append("\n".join(lines))

        if not sections:
            return ""

        total = len(all_tasks) + len(all_outcomes) + len(all_decisions) + len(open_blockers)
        header = (
            f"## Teamwork Graph  "
            f"({len(open_tasks)} open tasks · {len(open_blockers)} blockers · "
            f"{len(all_outcomes)} outcomes · {total} total entities)"
        )
        return header + "\n\n" + "\n\n".join(sections)

    except Exception:
        return ""
