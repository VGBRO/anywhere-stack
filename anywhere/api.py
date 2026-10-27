"""Anywhere Stack API — FastAPI server powering the prototype UI via NVIDIA Nemotron on Nebius."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from anywhere.client import reason, route, Model

app = FastAPI(title="Anywhere Stack", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve the prototype UI ────────────────────────────────────────────────────

PROTOTYPE = Path(__file__).parent.parent / "public" / "index.html"
DOWNLOADS_PROTOTYPE = Path.home() / "Downloads" / "anywhere_stack_v5.html"


@app.get("/")
def serve_ui():
    if PROTOTYPE.exists():
        return FileResponse(PROTOTYPE)
    if DOWNLOADS_PROTOTYPE.exists():
        return FileResponse(DOWNLOADS_PROTOTYPE)
    return {"status": "Anywhere Stack API running", "ui": "place index.html in public/"}


# ── Schemas ───────────────────────────────────────────────────────────────────

class Project(BaseModel):
    id: str
    name: str
    tags: list[str] = []
    state: str = ""
    goal: str = ""

class IntentRequest(BaseModel):
    text: str
    projects: list[Project] = []

class QueueItem(BaseModel):
    id: str
    text: str
    project_id: Optional[str] = None

class SyncRequest(BaseModel):
    queue: list[QueueItem]
    projects: list[Project] = []

# ── Prompts ───────────────────────────────────────────────────────────────────

ROUTER_SYSTEM = """You are a fast intent router for a personal AI agent called Anywhere Stack.

Given a user's natural language intent and a list of their active projects, determine:
1. Which project this intent belongs to (match by name, tags, or context)
2. Whether this creates a new project or updates an existing one
3. A one-line classification of the action type

Respond ONLY with valid JSON — no prose, no markdown.

Format:
{
  "project_id": "<id from the list, or 'new' if no match>",
  "project_name": "<matched project name, or suggested name for new project>",
  "is_new": <true|false>,
  "action_type": "<update|research|plan|task|decision>",
  "confidence": <0.0–1.0>
}"""

COS_SYSTEM = """You are the Chief of Staff for a personal AI operating system called Anywhere Stack.

You are powered by NVIDIA Nemotron on Nebius Token Factory.

Your job: given a user's intent and their project context, generate a rich, structured update for the Project Brain.

The Project Brain has five sections:
- goal: What the user is trying to accomplish long-term
- state: What is true right now (current situation, progress)
- decision: The guiding principle or direction for this project
- actions: Concrete next steps (3–5 bullet points)
- memory: Persistent facts, contacts, constraints that should never be lost

Generate a response that:
1. Acknowledges the intent naturally and warmly (1–2 sentences)
2. Updates the project brain sections that changed

Respond ONLY with valid JSON — no prose, no markdown.

Format:
{
  "response": "<warm acknowledgment, 1-2 sentences, feel free to use the dog's name Bira if it's an after-hours personal request>",
  "brain": {
    "goal": "<updated or unchanged goal>",
    "state": "<updated current state>",
    "decision": "<updated or unchanged direction>",
    "actions": ["<action 1>", "<action 2>", "<action 3>"],
    "memory": "<updated persistent facts>"
  }
}"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/api/intent")
def process_intent(req: IntentRequest):
    """
    Online intent processing — two-stage Nemotron pipeline:
    1. NANO model routes the intent to the right project (fast, ~100ms)
    2. ULTRA model generates the Project Brain update (deep, ~2s)
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Intent text required")

    # Stage 1: Fast routing with Nemotron NANO
    project_list = json.dumps([
        {"id": p.id, "name": p.name, "tags": p.tags}
        for p in req.projects
    ], indent=2)

    routing_prompt = f"""User intent: {req.text}

Active projects:
{project_list}

Route this intent."""

    try:
        routing_raw = route(routing_prompt, system=ROUTER_SYSTEM, model=Model.NANO)
        routing = json.loads(routing_raw.strip().strip("```json").strip("```").strip())
    except Exception as e:
        routing = {
            "project_id": "new",
            "project_name": "New Project",
            "is_new": True,
            "action_type": "plan",
            "confidence": 0.5,
        }

    # Find the matched project for context
    matched = next((p for p in req.projects if p.id == routing.get("project_id")), None)
    project_context = ""
    if matched:
        project_context = f"""Current project context:
- Goal: {matched.goal}
- State: {matched.state}
"""

    # Stage 2: Deep CoS reasoning with Nemotron ULTRA
    cos_prompt = f"""User intent: {req.text}

Project: {routing.get('project_name', 'New Project')}
{project_context}
Generate the Project Brain update."""

    try:
        cos_raw = reason(cos_prompt, system=COS_SYSTEM, model=Model.ULTRA)
        cos_result = json.loads(cos_raw.strip().strip("```json").strip("```").strip())
    except Exception as e:
        cos_result = {
            "response": f"Got it. I'll work on {routing.get('project_name', 'this')} for you.",
            "brain": {
                "goal": matched.goal if matched else "",
                "state": f"Intent captured: {req.text}",
                "decision": "",
                "actions": ["Review intent and define next steps."],
                "memory": "",
            },
        }

    return {
        "project_id": routing.get("project_id"),
        "project_name": routing.get("project_name"),
        "is_new": routing.get("is_new", False),
        "action_type": routing.get("action_type"),
        "routing_confidence": routing.get("confidence"),
        "response": cos_result.get("response", ""),
        "brain": cos_result.get("brain", {}),
        "models_used": {
            "router": Model.NANO.value,
            "cos": Model.ULTRA.value,
            "provider": "Nebius Token Factory",
        },
    }


@app.post("/api/sync")
def sync_queue(req: SyncRequest):
    """
    Process all queued offline intents through Nemotron when back online.
    Each queued intent runs through the full two-stage pipeline.
    """
    results = []
    for item in req.queue:
        intent_req = IntentRequest(text=item.text, projects=req.projects)
        try:
            result = process_intent(intent_req)
            results.append({"id": item.id, "status": "processed", **result})
        except Exception as e:
            results.append({"id": item.id, "status": "error", "error": str(e)})
    return {"synced": len(results), "results": results}


@app.get("/health")
def health():
    nebius_key_set = bool(os.getenv("NEBIUS_API_KEY"))
    return {
        "status": "ok",
        "nebius_configured": nebius_key_set,
        "models": {
            "router": Model.NANO.value,
            "cos": Model.ULTRA.value,
            "offline": "ollama/nemotron-mini (see offline.py)",
        },
        "provider": "Nebius Token Factory",
    }
