"""Regimes — auditable self-improvement loop.

Implements Yohei's Regimes pattern:
  1. Diagnose — query lineage for recurring failure patterns
  2. Propose   — ask LLM for a minimal behavioral fix
  3. Record    — emit proposal as a first-class event (regime.patch_proposed)
  4. Promote   — human or held-out test approves before any change lands

All proposals are events in the audit trail. Nothing changes automatically.

Two entry points:
  run_regimes_loop(portfolio_root)   — diagnoses portfolio-wide lineage failures
  run_teamwork_regimes(repo_path)    — diagnoses teamwork graph extraction quality
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional


def _diagnose_failures(portfolio_root: str, min_occurrences: int = 2) -> list[dict]:
    """Query lineage for recurring failure patterns."""
    from anywhere.state.canonical import query_lineage
    all_failures = (
        query_lineage(portfolio_root, event_type="task_failure")
        + query_lineage(portfolio_root, event_type="behavior_failure")
        + query_lineage(portfolio_root, event_type="behavior.failed")
    )
    if len(all_failures) < min_occurrences:
        return []

    # Group by error string (first 80 chars)
    patterns: dict[str, list[dict]] = {}
    for f in all_failures:
        key = (f.get("error") or f.get("reason") or "unknown")[:80]
        patterns.setdefault(key, []).append(f)

    return [
        {"pattern": k, "count": len(v), "examples": v[:3]}
        for k, v in patterns.items()
        if len(v) >= min_occurrences
    ]


def _propose_fix(pattern: dict) -> Optional[dict]:
    """Ask Nemotron Super to diagnose and propose a minimal fix."""
    from anywhere.client import reason, Model
    import re

    system = """You are a Regimes loop — a self-improvement agent that diagnoses recurring failures.
Given a recurring failure pattern, propose the smallest possible fix.

Respond in JSON only:
{
  "diagnosis": "root cause in one sentence",
  "fix_type": "config_change|prompt_update|code_change|retry_logic",
  "fix_description": "specific, actionable change (max 2 sentences)",
  "affected_component": "file or module",
  "confidence": "high|medium|low",
  "test_criterion": "how to verify the fix worked"
}"""

    prompt = (
        f"Recurring failure pattern:\n"
        f"Error: {pattern['pattern']}\n"
        f"Occurrences: {pattern['count']}\n"
        f"Examples (first 2):\n{json.dumps(pattern['examples'][:2], indent=2)}\n\n"
        f"Diagnose the root cause and propose a minimal fix."
    )

    raw = reason(prompt, system=system, model=Model.SUPER)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None


def run_regimes_loop(portfolio_root: str, min_occurrences: int = 2) -> dict:
    """Run one Regimes improvement cycle against the portfolio's lineage.

    Returns: {"patterns_found": int, "proposals": [proposal_dict, ...]}
    All proposals are persisted as regime.patch_proposed events.
    """
    from anywhere.state.canonical import append_event
    from rich.console import Console
    console = Console()

    console.print("\n[bold yellow]◆ Regimes Loop[/bold yellow]")

    patterns = _diagnose_failures(portfolio_root, min_occurrences)
    if not patterns:
        console.print("  [dim]No recurring failure patterns. Nothing to improve.[/dim]")
        append_event(portfolio_root, {"type": "regimes_run", "patterns_found": 0, "proposals": 0})
        return {"patterns_found": 0, "proposals": []}

    console.print(f"  Found [bold]{len(patterns)}[/bold] recurring pattern(s)")
    proposals = []

    for pattern in patterns:
        label = pattern["pattern"][:72]
        console.print(f"\n  [yellow]→[/yellow] ({pattern['count']}×) {label}")
        fix = _propose_fix(pattern)
        if not fix:
            console.print("    [dim]Could not generate fix proposal.[/dim]")
            continue
        proposal = {
            "pattern": pattern["pattern"],
            "occurrences": pattern["count"],
            "fix": fix,
            "status": "proposed",
        }
        proposals.append(proposal)
        conf = fix.get("confidence", "?")
        desc = fix.get("fix_description", "")[:80]
        console.print(f"    [green]Proposal ({conf}):[/green] {desc}")
        console.print(f"    [dim]Component: {fix.get('affected_component', 'unknown')}  "
                      f"Test: {fix.get('test_criterion', 'n/a')[:60]}[/dim]")

        # Emit proposal as a first-class event — nothing changes until approved
        append_event(portfolio_root, {
            "type": "regime.patch_proposed",
            "pattern": pattern["pattern"],
            "occurrences": pattern["count"],
            "fix": fix,
            "status": "proposed",
        })

    append_event(portfolio_root, {
        "type": "regimes_run",
        "patterns_found": len(patterns),
        "proposals": len(proposals),
    })

    console.print(f"\n  [bold]{len(proposals)}[/bold] proposal(s) recorded as [dim]regime.patch_proposed[/dim] events.")
    console.print("  [dim]Review: query_lineage(portfolio_root, event_type='regime.patch_proposed')[/dim]")

    return {"patterns_found": len(patterns), "proposals": proposals}


def run_teamwork_regimes(repo_path: str, min_occurrences: int = 2) -> dict:
    """Run one Regimes quality cycle against the teamwork graph.

    Sources of failure signal:
      - behavior.failed events in .teamwork.sqlite  (ActiveGraph runtime errors)
      - behavior.failed events in runs/*.json        (quality signals: extraction_empty)
      - github.fetch.error / github.pr.error in runs/*.json

    Groups by reason, proposes fixes for recurring patterns (>= min_occurrences).
    All proposals are emitted as regime.patch_proposed events — nothing auto-applies.

    Returns: {"patterns_found": int, "proposals": [proposal_dict, ...]}
    """
    from anywhere.state.canonical import append_event, read_recent_events
    from rich.console import Console
    console = Console()

    failures: list[dict] = []

    # 1. Pull behavior.failed from the teamwork SQLite (runtime exceptions)
    db_path = Path(repo_path) / ".teamwork.sqlite"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            rows = conn.execute(
                "SELECT payload FROM events WHERE type IN ('behavior.failed', 'behavior.error')"
            ).fetchall()
            conn.close()
            for (payload_json,) in rows:
                p = json.loads(payload_json) if payload_json else {}
                # ActiveGraph behavior.failed payload: {behavior: ..., reason: exception.XYZ}
                failures.append({
                    "type":     "behavior.failed",
                    "behavior": p.get("behavior", ""),
                    "reason":   p.get("reason", ""),
                    "source":   "teamwork.sqlite",
                })
        except Exception:
            pass

    # 2. Pull quality + error events from the canonical run log
    recent = read_recent_events(repo_path, n=200)
    _QUALITY_TYPES = {"behavior.failed", "github.fetch.error", "github.pr.error"}
    for event in recent:
        if event.get("type") in _QUALITY_TYPES:
            failures.append(event)

    if not failures:
        return {"patterns_found": 0, "proposals": []}

    # Group by reason/error string
    patterns: dict[str, list[dict]] = {}
    for f in failures:
        key = (f.get("reason") or f.get("error") or f.get("type", "unknown"))[:80]
        patterns.setdefault(key, []).append(f)

    recurring = [
        {"pattern": k, "count": len(v), "examples": v[:3]}
        for k, v in patterns.items()
        if len(v) >= min_occurrences
    ]

    if not recurring:
        append_event(repo_path, {
            "type": "teamwork_regimes_run",
            "patterns_found": 0,
            "proposals": 0,
        })
        return {"patterns_found": 0, "proposals": []}

    console.print(f"\n[bold yellow]◆ Teamwork Regimes[/bold yellow] — {len(recurring)} pattern(s)")
    proposals: list[dict] = []

    for pattern in recurring:
        label = pattern["pattern"][:72]
        console.print(f"  [yellow]→[/yellow] ({pattern['count']}×) {label}")
        fix = _propose_fix(pattern)
        if not fix:
            continue
        proposal = {
            "pattern":     pattern["pattern"],
            "occurrences": pattern["count"],
            "fix":         fix,
            "status":      "proposed",
        }
        proposals.append(proposal)
        console.print(
            f"    [green]Proposal ({fix.get('confidence')}):[/green] "
            f"{fix.get('fix_description', '')[:80]}"
        )
        append_event(repo_path, {
            "type":        "regime.patch_proposed",
            "pattern":     pattern["pattern"],
            "occurrences": pattern["count"],
            "fix":         fix,
            "status":      "proposed",
            "scope":       "teamwork_graph",
        })

    append_event(repo_path, {
        "type":             "teamwork_regimes_run",
        "patterns_found":   len(recurring),
        "proposals":        len(proposals),
    })

    return {"patterns_found": len(recurring), "proposals": proposals}
