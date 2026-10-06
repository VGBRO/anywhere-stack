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
graph_app = typer.Typer(help="Teamwork Graph — status, disputes, and queries.")
app.add_typer(graph_app, name="graph")
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
def schedule(
    hour: int = typer.Option(8, "--hour", "-h", help="Hour to run daily (24h, local time)"),
    uninstall: bool = typer.Option(False, "--uninstall", help="Remove the scheduled job"),
):
    """Install (or remove) a daily launchd job that runs the CoS heartbeat automatically."""
    import subprocess
    import textwrap

    label = "com.anywhere-stack.heartbeat"
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    project_root = Path(__file__).parent.parent.resolve()
    uv_bin = "/Users/vguruvugari/.local/bin/uv"
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    if uninstall:
        try:
            subprocess.run(["launchctl", "unload", str(plist_path)], check=False, capture_output=True)
        except Exception:
            pass
        if plist_path.exists():
            plist_path.unlink()
        console.print(f"[yellow]✓ Removed scheduled heartbeat[/yellow] ({plist_path})")
        return

    plist = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{label}</string>
            <key>ProgramArguments</key>
            <array>
                <string>{uv_bin}</string>
                <string>--directory</string>
                <string>{project_root}</string>
                <string>run</string>
                <string>anywhere</string>
                <string>heartbeat</string>
            </array>
            <key>WorkingDirectory</key>
            <string>{project_root}</string>
            <key>StartCalendarInterval</key>
            <dict>
                <key>Hour</key>
                <integer>{hour}</integer>
                <key>Minute</key>
                <integer>0</integer>
            </dict>
            <key>StandardOutPath</key>
            <string>{log_dir}/heartbeat.log</string>
            <key>StandardErrorPath</key>
            <string>{log_dir}/heartbeat.err</string>
            <key>EnvironmentVariables</key>
            <dict>
                <key>HOME</key>
                <string>{Path.home()}</string>
                <key>PATH</key>
                <string>/usr/local/bin:/usr/bin:/bin:/Users/vguruvugari/.local/bin</string>
            </dict>
        </dict>
        </plist>
    """)

    plist_path.write_text(plist)

    # Unload existing job silently before reloading
    subprocess.run(["launchctl", "unload", str(plist_path)], check=False, capture_output=True)
    result = subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True, text=True)

    if result.returncode == 0:
        console.print(f"[green]✓ Heartbeat scheduled daily at {hour:02d}:00[/green]")
        console.print(f"  Plist:  {plist_path}")
        console.print(f"  Logs:   {log_dir}/heartbeat.log")
        console.print(f"  Remove: [dim]anywhere schedule --uninstall[/dim]")
    else:
        console.print(f"[red]✗ launchctl load failed:[/red] {result.stderr.strip()}")
        console.print(f"  Plist written to {plist_path} — load manually if needed")


@app.command()
def regimes(
    min_occurrences: int = typer.Option(2, "--min", "-m", help="Minimum occurrences to flag a failure pattern"),
):
    """Run the Regimes self-improvement loop — diagnose failure patterns and propose fixes."""
    console.print("[bold yellow]Running Regimes self-improvement loop...[/bold yellow]")
    from anywhere.regimes import run_regimes_loop
    result = run_regimes_loop(PORTFOLIO_ROOT, min_occurrences=min_occurrences)
    console.print(f"\n[dim]Patterns diagnosed: {result['patterns_found']}  "
                  f"Proposals recorded: {len(result.get('proposals', []))}[/dim]")


@app.command()
def topology():
    """Show the role coordination topology (typed graph edges)."""
    from anywhere.relations import ROLE_RELATIONS
    from anywhere.runtime import registered_behaviors
    import anywhere.behaviors  # register handlers

    console.print("\n[bold]Role Topology (typed graph edges):[/bold]")
    for r in ROLE_RELATIONS:
        console.print(f"  {r.source:8s} --({r.rel_type})--> {r.target:8s}  on: {r.on_event}")

    console.print("\n[bold]Registered behaviors:[/bold]")
    for event_type, fns in registered_behaviors().items():
        console.print(f"  [cyan]{event_type}[/cyan] → {', '.join(fns)}")


@app.command()
def slack():
    """Start the Slack Socket Mode listener."""
    console.print("[bold]Starting Anywhere Stack Slack listener...[/bold]")
    console.print(f"Portfolio root: {PORTFOLIO_ROOT}")
    from anywhere.interfaces.slack import start_slack_listener
    start_slack_listener()


@graph_app.command("status")
def graph_status(
    path: str = typer.Argument(".", help="Path to project repo"),
):
    """Show teamwork graph: open tasks, blockers, recent outcomes, disputed entities."""
    from anywhere.state.canonical import read_teamwork_graph
    content = read_teamwork_graph(path)
    if not content:
        console.print(f"[dim]No teamwork graph found at[/dim] {path}")
        console.print("[dim]Add .teamwork_config.json and run a heartbeat to ingest signals.[/dim]")
        raise typer.Exit(0)
    console.print(content)


@graph_app.command("dispute")
def graph_dispute(
    entity_id: str = typer.Argument(..., help="Entity ID to dispute (e.g. task#00000001)"),
    reason: str = typer.Argument(..., help="Reason for disputing this entity"),
    path: str = typer.Option(".", "--path", "-p", help="Path to project repo"),
    who: str = typer.Option("human", "--by", help="Who is raising the dispute"),
):
    """Mark a teamwork entity as disputed.

    The disputed flag appears in `graph status` output as ⚠ and feeds the
    Regimes quality loop as a signal that extraction needs improvement.
    Disputes are non-destructive — the original entity is never deleted.
    """
    from anywhere.state.canonical import dispute_entity
    dispute_entity(path, entity_id, reason, disputed_by=who)
    console.print(f"[yellow]⚠  Disputed:[/yellow] {entity_id}")
    console.print(f"   Reason:  {reason}")
    console.print(f"   By:      {who}")
    console.print(
        f"   [dim]Entity marked in runs/ — visible in next `anywhere graph status {path}`[/dim]"
    )


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
