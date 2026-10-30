"""Reactive behaviors — Layer 3 of the ActiveGraph pattern.

Behaviors fire on events; they never call each other directly.
Coordination is implicit: a behavior emits events; those events fire other behaviors.

Registration happens at import time via @on decorators in anywhere.runtime.
"""

import traceback
from anywhere.runtime import on
from anywhere.state.canonical import append_event


# ── CoS behaviors ─────────────────────────────────────────────────────────────

@on("portfolio.heartbeat_requested")
def cos_surveys_portfolio(event: dict, context: dict) -> list[dict]:
    """CoS scans the portfolio and emits triage requests for projects needing attention."""
    from anywhere.roles.cos import _load_portfolio, _load_github_signals
    from anywhere.client import reason, Model
    from anywhere.state.canonical import parse_json
    from pathlib import Path

    portfolio_root = context.get("portfolio_root") or event.get("portfolio_root", "")
    portfolio = _load_portfolio(portfolio_root)
    if not portfolio:
        return [{"type": "portfolio.empty", "portfolio_root": portfolio_root}]

    portfolio_text = "\n\n---\n\n".join(
        f"## Project: {name}\n{content}" for name, content in portfolio.items()
    )
    github_signals = _load_github_signals()
    if github_signals and not github_signals.startswith("(GitHub"):
        portfolio_text += f"\n\n---\n\n## GitHub Open Issues\n{github_signals}"

    skill_path = Path(__file__).parent.parent.parent / "skills" / "cos-skill.md"
    role_skill = skill_path.read_text() if skill_path.exists() else ""

    system = f"""You are the Chief of Staff. Survey the portfolio and determine what requires attention.
{f"Role skill:{chr(10)}{role_skill}" if role_skill else ""}
Respond in JSON:
{{
  "attention_required": [
    {{"project": "name", "reason": "why", "action": "dispatch_pm|escalate_human|monitor", "urgency": "high|medium|low"}}
  ],
  "escalations": ["thing requiring human judgment"],
  "portfolio_health": "green|yellow|red",
  "summary": "one sentence portfolio status"
}}"""

    try:
        raw = reason(portfolio_text, system=system, model=Model.ULTRA)
        result = parse_json(raw) or {
            "attention_required": [], "escalations": [], "portfolio_health": "yellow", "summary": raw[:200]
        }
    except Exception as e:
        append_event(portfolio_root, {"type": "cos_error", "error": str(e), "traceback": traceback.format_exc()})
        return [{"type": "behavior.failed", "behavior": "cos_surveys_portfolio", "error": str(e)}]

    append_event(portfolio_root, {
        "type": "cos_heartbeat",
        "portfolio_health": result.get("portfolio_health", "yellow"),
        "summary": result.get("summary", ""),
        "escalations": result.get("escalations", []),
    })

    emitted: list[dict] = []
    for item in result.get("attention_required", []):
        if item.get("action") == "dispatch_pm" and item.get("urgency") in ("high", "medium"):
            project_path = str(Path(portfolio_root) / item["project"])
            if Path(project_path).exists():
                emitted.append({
                    "type": "project.needs_triage",
                    "project": item["project"],
                    "project_path": project_path,
                    "reason": item.get("reason", ""),
                    "urgency": item.get("urgency", "medium"),
                })

    for escalation in result.get("escalations", []):
        emitted.append({"type": "escalation.required", "message": escalation, "source": "cos"})

    return emitted


# ── PM behaviors ──────────────────────────────────────────────────────────────

@on("project.needs_triage")
def pm_triages_project(event: dict, context: dict) -> list[dict]:
    """PM triages a project and delegates bounded tasks to Builder."""
    from anywhere.roles.pm import run_pm_triage

    repo_path = event.get("project_path", "")
    if not repo_path:
        return [{"type": "behavior.failed", "behavior": "pm_triages_project",
                 "error": "no project_path in event", "event": event}]

    try:
        result = run_pm_triage(repo_path)
    except Exception as e:
        append_event(repo_path, {
            "type": "task_failure",
            "behavior": "pm_triages_project",
            "error": str(e),
            "traceback": traceback.format_exc(),
        })
        return [{"type": "task.failed", "repo_path": repo_path, "error": str(e),
                 "triggering": event}]

    emitted = [{"type": "project.triaged", "project_path": repo_path,
                "health": result.get("health", "unknown")}]

    builder_result = result.get("builder_result")
    if builder_result:
        conf = builder_result.get("confidence", "low")
        if conf in ("high", "medium"):
            emitted.append({"type": "task.completed", "repo_path": repo_path,
                             "confidence": conf, "output": builder_result.get("output", "")})
        else:
            emitted.append({"type": "task.low_confidence", "repo_path": repo_path,
                             "confidence": conf})

    return emitted


# ── Failure audit behaviors ───────────────────────────────────────────────────

@on("behavior.failed")
def record_behavior_failure(event: dict, context: dict) -> list[dict]:
    """Persist behavior failures as first-class events in the event log."""
    repo_path = context.get("repo_path") or event.get("repo_path", "")
    if repo_path:
        try:
            append_event(repo_path, {
                "type": "behavior_failure",
                "behavior": event.get("behavior", "unknown"),
                "triggering_event_type": event.get("triggering_event_type", ""),
                "error": event.get("error", ""),
            })
        except Exception:
            pass
    return []


@on("task.failed")
def record_task_failure(event: dict, context: dict) -> list[dict]:
    """Persist task failures as first-class events and push to Slack."""
    repo_path = event.get("repo_path", "")
    error = event.get("error", "")
    if repo_path:
        try:
            append_event(repo_path, {
                "type": "task_failure",
                "task": event.get("task", {}),
                "error": error,
            })
        except Exception:
            pass
    from pathlib import Path
    from anywhere.notify import post_to_slack
    project = Path(repo_path).name if repo_path else "unknown"
    post_to_slack(f"🔴 *Task failed* in `{project}`\n```{error[:300]}```")
    return []
