"""Chief of Staff role — portfolio-level attention routing across all projects.

Coordination model (Yohei/ActiveGraph):
  CoS reasons about the portfolio, then EMITS events rather than calling roles directly.
  The runtime.run_until_idle() loop fires the PM behavior reactively.
  No component instructs another; coordination happens through the shared event queue.
"""

import json
from pathlib import Path
from rich.console import Console
from anywhere.client import reason, route, Model
from anywhere.state.canonical import append_event, parse_json, read_state, read_brief
from anywhere.tools.github import list_my_repos, list_issues as github_list_issues

console = Console()


def _load_github_signals() -> str:
    """Pull open issues from all GitHub repos owned by the configured user."""
    try:
        raw = list_my_repos()
        repos = json.loads(raw) if raw.startswith("[") else []
        lines = []
        for repo in repos:
            if repo.get("open_issues", 0) > 0:
                issues_raw = github_list_issues(repo["name"])
                lines.append(f"### GitHub: {repo['full_name']} ({repo['open_issues']} open issues)")
                lines.append(issues_raw)
        return "\n\n".join(lines) if lines else ""
    except Exception as e:
        return f"(GitHub unavailable: {e})"


def _load_portfolio(portfolio_root: str) -> dict[str, str]:
    """Load state projections from all registered project repos."""
    portfolio = {}
    root = Path(portfolio_root)
    for project_dir in sorted(root.iterdir()):
        if project_dir.is_dir() and not project_dir.name.startswith("."):
            brief = read_brief(str(project_dir))
            state = read_state(str(project_dir))
            portfolio[project_dir.name] = f"### {project_dir.name}\n\n{state}\n\n{brief}"
    return portfolio


def run_cos_heartbeat(portfolio_root: str) -> dict:
    """
    Chief of Staff heartbeat.
    Reads all project projections, detects what needs attention,
    dispatches project-level heartbeats where needed, escalates to human.
    """
    console.print("\n[bold magenta]◆ Chief of Staff Heartbeat[/bold magenta]")
    portfolio = _load_portfolio(portfolio_root)

    if not portfolio:
        console.print("  [yellow]No projects found in portfolio root.[/yellow]")
        return {"escalations": [], "dispatched": [], "summary": "Empty portfolio."}

    # Build portfolio summary for CoS reasoning
    portfolio_text = "\n\n---\n\n".join(
        f"## Project: {name}\n{content}" for name, content in portfolio.items()
    )

    # Append GitHub signals if available
    console.print("  [dim]Fetching GitHub signals...[/dim]")
    github_signals = _load_github_signals()
    if github_signals and not github_signals.startswith("(GitHub"):
        portfolio_text += f"\n\n---\n\n## GitHub Open Issues\n{github_signals}"

    skill_path = Path(__file__).parent.parent.parent / "skills" / "cos-skill.md"
    role_skill = skill_path.read_text() if skill_path.exists() else ""

    system = f"""You are the Chief of Staff. Your job is to survey the portfolio, detect what requires attention, and determine what to dispatch or escalate.

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

    prompt = f"Survey this portfolio and determine what requires attention:\n\n{portfolio_text}"
    console.print("  [dim]Reasoning with Nemotron Ultra...[/dim]")
    raw = reason(prompt, system=system, model=Model.ULTRA)

    result = parse_json(raw)
    if not result:
        result = {"attention_required": [], "escalations": [(raw or "")[:300]], "portfolio_health": "yellow", "summary": "CoS heartbeat completed (parse error)."}

    # Reactive dispatch — emit events; behaviors fire through the runtime
    import anywhere.behaviors  # register @on handlers
    from anywhere.runtime import run_until_idle

    dispatched = []
    for item in result.get("attention_required", []):
        if item.get("action") == "dispatch_pm" and item.get("urgency") in ("high", "medium"):
            project_path = str(Path(portfolio_root) / item["project"])
            if Path(project_path).exists():
                console.print(f"  [blue]→ Dispatching PM (reactive):[/blue] {item['project']} ({item['reason']})")
                pm_events = run_until_idle(
                    initial_events=[{
                        "type": "project.needs_triage",
                        "project": item["project"],
                        "project_path": project_path,
                        "reason": item.get("reason", ""),
                        "urgency": item.get("urgency", "medium"),
                    }],
                    context={"portfolio_root": portfolio_root, "repo_path": project_path},
                )
                dispatched.append(item["project"])
                completed = [e for e in pm_events if e.get("type") == "task.completed"]
                low_conf = [e for e in pm_events if e.get("type") == "task.low_confidence"]
                failures = [e for e in pm_events if e.get("type") in ("task.failed", "behavior.failed")]
                if completed:
                    conf = completed[0].get("confidence", "?")
                    console.print(f"    [cyan]→ Task completed ({conf} confidence)[/cyan]")
                elif low_conf:
                    console.print(f"    [yellow]→ Task completed with low confidence[/yellow]")
                elif failures:
                    console.print(f"    [red]→ Failure recorded: {failures[0].get('error', '')[:80]}[/red]")

    health = result.get("portfolio_health", "green")
    summary = result.get("summary", "Heartbeat complete.")
    health_color = {"green": "green", "yellow": "yellow", "red": "red"}.get(health, "white")
    console.print(f"\n  [{health_color}]◆ Portfolio: {health.upper()}[/{health_color}] — {summary}")

    escalations = result.get("escalations", [])
    if escalations:
        console.print("\n  [bold red]⚠ Requires human judgment:[/bold red]")
        for e in escalations:
            console.print(f"    • {e}")

    append_event(portfolio_root, {
        "type": "cos_heartbeat",
        "portfolio_health": health,
        "dispatched": dispatched,
        "escalations": escalations,
        "summary": summary,
    })

    # Proactive Slack post — system pushes results without waiting to be asked
    from anywhere.notify import post_to_slack
    health_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(health, "⚪")
    lines = [f"{health_emoji} *Heartbeat complete* — {summary}"]
    if dispatched:
        lines.append(f"Dispatched PM: {', '.join(dispatched)}")
    if escalations:
        lines.append("*⚠ Needs your attention:*")
        lines.extend(f"• {e}" for e in escalations)
    post_to_slack("\n".join(lines))

    return {"escalations": escalations, "dispatched": dispatched, "summary": summary, "health": health}
