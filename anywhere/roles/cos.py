"""Chief of Staff role — portfolio-level attention routing across all projects."""

import json
from pathlib import Path
from rich.console import Console
from anywhere.client import reason, route, Model
from anywhere.heartbeat import run_project_heartbeat
from anywhere.state.canonical import append_event, read_state, read_brief

console = Console()


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

    try:
        raw_clean = raw.strip()
        if "```" in raw_clean:
            raw_clean = raw_clean.split("```")[1]
            if raw_clean.startswith("json"):
                raw_clean = raw_clean[4:]
        result = json.loads(raw_clean.strip())
    except Exception:
        result = {"attention_required": [], "escalations": [raw[:300]], "portfolio_health": "yellow", "summary": "CoS heartbeat completed (parse error)."}

    dispatched = []
    for item in result.get("attention_required", []):
        if item.get("action") == "dispatch_pm" and item.get("urgency") in ("high", "medium"):
            project_path = str(Path(portfolio_root) / item["project"])
            if Path(project_path).exists():
                console.print(f"  [blue]→ Dispatching PM heartbeat:[/blue] {item['project']} ({item['reason']})")
                run_project_heartbeat(project_path, role="project_manager")
                dispatched.append(item["project"])

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

    return {"escalations": escalations, "dispatched": dispatched, "summary": summary, "health": health}
