"""Slack interface — the mobile remote for the Anywhere Stack."""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from anywhere.client import route, reason, Model
from anywhere.roles.cos import run_cos_heartbeat
from anywhere.heartbeat import run_project_heartbeat
from anywhere.state.canonical import append_event
from anywhere.audio import is_audio_file, transcribe_audio

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
COS_SLACK_CHANNEL = os.getenv("COS_SLACK_CHANNEL", "#anywhere-stack")
PORTFOLIO_ROOT = os.getenv("PORTFOLIO_ROOT", str(Path.home() / "claude" / "anywhere-stack" / "projects"))

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


def _classify_message(text: str) -> dict:
    """Classify an incoming message as directive, question, approval, status, or heartbeat."""
    system = (
        "Classify this message from the human operator of an agentic system. "
        "Use type 'heartbeat' if the message is asking to run a heartbeat, health check, or portfolio check. "
        "Respond in JSON: {\"type\": \"heartbeat|directive|question|approval|status|unknown\", \"project\": \"project name or null\", \"summary\": \"one line summary\"}"
    )
    raw = route(text, system=system, model=Model.LIGHTNING)
    from anywhere.state.canonical import parse_json
    result = parse_json(raw)
    return result if result else {"type": "unknown", "project": None, "summary": text[:100]}


def _handle_directive(text: str, project: str | None) -> str:
    """Convert a human directive into a task and route it."""
    system = (
        "Convert this human directive into a structured task packet for the project manager. "
        "Respond in JSON: {\"objective\": \"...\", \"constraints\": \"...\", \"authority\": \"what the PM may decide\", \"acceptance\": \"how completion is verified\"}"
    )
    task = route(text, system=system, model=Model.NANO)

    if project:
        project_path = str(Path(PORTFOLIO_ROOT) / project)
        if Path(project_path).exists():
            append_event(project_path, {"type": "human_directive", "directive": text, "task": task})
            return f"Directive recorded for *{project}*. PM will pick it up on next heartbeat.\n```{task}```"

    return f"Directive received. No matching project found — please specify a project name.\n```{task}```"


def _handle_status(project: str | None) -> str:
    """Return current status for a project or the full portfolio."""
    if project:
        project_path = Path(PORTFOLIO_ROOT) / project
        if project_path.exists():
            brief_file = project_path / "brief.md"
            if brief_file.exists():
                return f"*{project}* status:\n\n{brief_file.read_text()[:1500]}"
        return f"Project `{project}` not found. Available: {', '.join(p.name for p in Path(PORTFOLIO_ROOT).iterdir() if p.is_dir())}"

    # Portfolio-level status
    lines = [f"*Portfolio Status*\n"]
    root = Path(PORTFOLIO_ROOT)
    for p in sorted(root.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            state_file = p / "state.md"
            if state_file.exists():
                first_line = state_file.read_text().split("\n")[2] if state_file.exists() else "no state"
                lines.append(f"• *{p.name}*: {first_line[:100]}")
    return "\n".join(lines) if len(lines) > 1 else "No projects found."


@app.event("app_mention")
def handle_mention(event, say):
    text = event.get("text", "")
    user = event.get("user", "human")

    classified = _classify_message(text)
    msg_type = classified.get("type", "unknown")
    project = classified.get("project")

    if msg_type == "directive":
        response = _handle_directive(text, project)
    elif msg_type == "status":
        response = _handle_status(project)
    elif msg_type == "approval":
        if project:
            project_path = str(Path(PORTFOLIO_ROOT) / project)
            if Path(project_path).exists():
                append_event(project_path, {"type": "human_approval", "message": text, "user": user})
                response = f"Approval recorded for *{project}*."
            else:
                response = f"Project `{project}` not found."
        else:
            response = "Approval received — please specify a project name."
    elif msg_type == "question":
        system = "You are the Chief of Staff answering a question about the portfolio. Be concise and factual."
        status_context = _handle_status(project)
        response = reason(f"Question: {text}\n\nContext:\n{status_context}", system=system, model=Model.SUPER)
    else:
        response = f"Received: `{text[:100]}`. Type `@anywhere-stack status` for portfolio status, or send a directive."

    say(response)


@app.message("heartbeat")
def handle_heartbeat_command(message, say):
    """Manual heartbeat trigger via Slack message."""
    text = message.get("text", "")
    say("Running CoS heartbeat across portfolio...")
    result = run_cos_heartbeat(PORTFOLIO_ROOT)
    health = result.get("health", "green")
    summary = result.get("summary", "Complete.")
    dispatched = result.get("dispatched", [])
    escalations = result.get("escalations", [])

    lines = [f"*Heartbeat complete* — Portfolio: *{health.upper()}*", f"_{summary}_"]
    if dispatched:
        lines.append(f"\nDispatched PM heartbeats: {', '.join(dispatched)}")
    if escalations:
        lines.append("\n*Requires your attention:*")
        for e in escalations:
            lines.append(f"• {e}")

    say("\n".join(lines))


@app.event("file_shared")
def handle_audio_note(event, say, client):
    """Handle Slack audio notes — transcribe and route through the agent pipeline."""
    file_id = event.get("file_id") or (event.get("file") or {}).get("id")
    if not file_id:
        return

    try:
        file_info = client.files_info(file=file_id)["file"]
    except Exception:
        return

    mimetype = file_info.get("mimetype", "")
    if not is_audio_file(mimetype):
        return

    channel = event.get("channel_id") or COS_SLACK_CHANNEL
    say(channel=channel, text="_Heard you. Transcribing audio note..._")

    # Download the private audio file using the bot token
    url = file_info.get("url_private_download") or file_info.get("url_private")
    if not url:
        say(channel=channel, text="Could not retrieve audio file URL.")
        return

    audio_response = requests.get(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"})
    if not audio_response.ok:
        say(channel=channel, text=f"Failed to download audio file (HTTP {audio_response.status_code}).")
        return

    try:
        filename = file_info.get("name", "audio.m4a")
        transcript = transcribe_audio(audio_response.content, filename=filename)
    except RuntimeError as e:
        say(channel=channel, text=f"Transcription not configured: {e}")
        return
    except Exception as e:
        say(channel=channel, text=f"Transcription failed: {e}")
        return

    say(channel=channel, text=f"_Transcribed:_ \"{transcript}\"")

    # Route through the same pipeline as a text message
    classified = _classify_message(transcript)
    msg_type = classified.get("type", "unknown")
    project = classified.get("project")

    if msg_type == "heartbeat":
        say(channel=channel, text="Running CoS heartbeat across portfolio...")
        result = run_cos_heartbeat(PORTFOLIO_ROOT)
        health = result.get("health", "green")
        summary = result.get("summary", "Complete.")
        dispatched = result.get("dispatched", [])
        escalations = result.get("escalations", [])
        lines = [f"*Heartbeat complete* — Portfolio: *{health.upper()}*", f"_{summary}_"]
        if dispatched:
            lines.append(f"\nDispatched PM heartbeats: {', '.join(dispatched)}")
        if escalations:
            lines.append("\n*Requires your attention:*")
            for e in escalations:
                lines.append(f"• {e}")
        response = "\n".join(lines)
    elif msg_type == "directive":
        response = _handle_directive(transcript, project)
    elif msg_type == "status":
        response = _handle_status(project)
    elif msg_type == "question":
        system = "You are the Chief of Staff answering a question about the portfolio. Be concise and factual."
        response = reason(f"Question: {transcript}\n\nContext:\n{_handle_status(project)}", system=system, model=Model.SUPER)
    else:
        response = f"Got it: \"{transcript[:200]}\". If this is a directive, try prefixing with a project name."

    say(channel=channel, text=response)


def post_to_cos_channel(message: str) -> None:
    """Post a message to the CoS Slack channel."""
    app.client.chat_postMessage(channel=COS_SLACK_CHANNEL, text=message)


def start_slack_listener():
    """Start the Slack Socket Mode listener."""
    if not SLACK_APP_TOKEN:
        raise RuntimeError("SLACK_APP_TOKEN not set. See .env.example.")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
