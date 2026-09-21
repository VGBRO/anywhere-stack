"""CLI entry point for the Anywhere Stack."""

import os
from pathlib import Path
import typer
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(
    name="anywhere",
    help="Repo-centric modular agent stack — powered by NVIDIA Nemotron on Nebius.",
    no_args_is_help=True,
)
console = Console()

PORTFOLIO_ROOT = os.getenv(
    "PORTFOLIO_ROOT",
    str(Path(__file__).parent.parent / "projects"),
)


@app.command()
def heartbeat(
    project: str = typer.Argument(None, help="Project name (runs CoS heartbeat if omitted)"),
    role: str = typer.Option("project_manager", "--role", "-r", help="Role to run: cos, project_manager, builder"),
):
    """Run a heartbeat — CoS (portfolio) or project-level."""
    if project is None or role == "cos":
        console.print("[bold magenta]Running Chief of Staff heartbeat...[/bold magenta]")
        from anywhere.roles.cos import run_cos_heartbeat
        run_cos_heartbeat(PORTFOLIO_ROOT)
    else:
        project_path = str(Path(PORTFOLIO_ROOT) / project)
        if not Path(project_path).exists():
            console.print(f"[red]Project not found:[/red] {project_path}")
            raise typer.Exit(1)
        console.print(f"[bold blue]Running {role} heartbeat for {project}...[/bold blue]")
        if role == "project_manager":
            from anywhere.roles.pm import run_pm_triage
            result = run_pm_triage(project_path)
            health = result.get("health", "green")
            health_color = {"green": "green", "yellow": "yellow", "red": "red"}.get(health, "white")
            console.print(f"  [{health_color}]● {health.upper()}[/{health_color}] {result.get('recommended_action', '')}")
            if result.get("builder_dispatched"):
                console.print(f"  [cyan]→ Builder completed:[/cyan] {result.get('priority_issue', {}).get('title', 'task')}")
        else:
            from anywhere.heartbeat import run_project_heartbeat
            run_project_heartbeat(project_path, role=role)


@app.command()
def status(
    project: str = typer.Argument(None, help="Project name (shows all if omitted)"),
):
    """Show current status of a project or the full portfolio."""
    root = Path(PORTFOLIO_ROOT)
    if project:
        project_path = root / project
        if not project_path.exists():
            console.print(f"[red]Project not found:[/red] {project}")
            raise typer.Exit(1)
        brief = (project_path / "brief.md").read_text() if (project_path / "brief.md").exists() else "No brief yet."
        console.print(f"\n[bold]{project}[/bold]\n{brief}")
    else:
        console.print(f"\n[bold]Portfolio Status[/bold] ({PORTFOLIO_ROOT})\n")
        for p in sorted(root.iterdir()):
            if p.is_dir() and not p.name.startswith("."):
                state_file = p / "state.md"
                health = "?"
                if state_file.exists():
                    for line in state_file.read_text().split("\n"):
                        if "health:" in line:
                            health = line.split(":")[-1].strip()
                            break
                color = {"green": "green", "yellow": "yellow", "red": "red"}.get(health, "dim")
                console.print(f"  [{color}]●[/{color}] {p.name} ({health})")


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    mission: str = typer.Option("", "--mission", "-m", help="One-line project mission"),
):
    """Initialize a new project repo with the canonical module structure."""
    project_path = Path(PORTFOLIO_ROOT) / name
    if project_path.exists():
        console.print(f"[yellow]Project already exists:[/yellow] {project_path}")
        raise typer.Exit(1)

    dirs = ["issues", "runs", "contracts", "claims", "evidence", "memory"]
    for d in dirs:
        (project_path / d).mkdir(parents=True)

    (project_path / "agent-os.md").write_text(
        f"# {name}\n\n## Mission\n{mission or 'TODO: describe the mission'}\n\n"
        "## Roles\n- Project Manager: reconcile state, sequence work, delegate\n"
        "- Builder: implement bounded tasks, record evidence\n\n"
        "## Invariants\n- Record all decisions with evidence\n"
        "- Never modify acceptance criteria without human approval\n\n"
        "## Next Action\nRun `anywhere heartbeat {name}` to initialize state.\n"
    )
    (project_path / "decisions.md").write_text(
        f"# Decision Log — {name}\n\n_Append only. Format: Date · Decision · Evidence · Implications_\n"
    )
    (project_path / "brief.md").write_text(
        f"# {name} — Brief\n\n_Not yet generated. Run `anywhere heartbeat {name}` to generate._\n"
    )
    (project_path / "state.md").write_text(
        f"---\nphase: SETUP\nhealth: green\nlast_update: \nblocker: none\nnext_action: bootstrap project\n---\n"
    )

    console.print(f"[green]✓ Project initialized:[/green] {project_path}")
    console.print(f"  Next: edit [bold]{name}/agent-os.md[/bold] then run [bold]anywhere heartbeat {name}[/bold]")


@app.command()
def slack():
    """Start the Slack Socket Mode listener."""
    console.print("[bold]Starting Anywhere Stack Slack listener...[/bold]")
    console.print(f"Portfolio root: {PORTFOLIO_ROOT}")
    from anywhere.interfaces.slack import start_slack_listener
    start_slack_listener()


@app.command()
def test_nebius():
    """Test Nebius Token Factory connection and available Nemotron models."""
    console.print("[bold]Testing Nebius Token Factory connection...[/bold]")
    from anywhere.client import get_client, Model
    client = get_client()
    models = client.models.list()
    nvidia_models = [m.id for m in models.data if "nvidia" in m.id.lower() or "nemotron" in m.id.lower()]
    console.print(f"\n[green]✓ Connected to Nebius Token Factory[/green]")
    console.print(f"\nNVIDIA / Nemotron models available ({len(nvidia_models)}):")
    for m in nvidia_models:
        console.print(f"  • {m}")

    console.print("\n[dim]Running test completion with Nemotron Nano...[/dim]")
    from anywhere.client import route
    response = route("Reply with exactly: ANYWHERE STACK ONLINE", model=Model.NANO)
    console.print(f"\n[green]✓ Test completion:[/green] {response.strip()}")
