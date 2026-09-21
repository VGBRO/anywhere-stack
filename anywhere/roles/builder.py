"""Builder role — bounded task execution within a project repo."""

import json
from pathlib import Path
from anywhere.client import reason, Model
from anywhere.state.canonical import append_event, read_agent_os, read_state


def execute_task(repo_path: str, task: dict) -> dict:
    """
    Execute a bounded task within a project repo.
    Returns a result dict with output, evidence, and state delta.
    """
    agent_os = read_agent_os(repo_path)
    state = read_state(repo_path)

    skill_path = Path(__file__).parent.parent.parent / "skills" / "builder-skill.md"
    role_skill = skill_path.read_text() if skill_path.exists() else ""

    contracts_path = Path(__file__).parent.parent.parent / "contracts" / "builder.md"
    contract = contracts_path.read_text() if contracts_path.exists() else ""

    system = f"""You are a Builder executing a bounded task in a project repo.
Your authority: implement what is asked, record evidence, do not alter acceptance criteria or project invariants.

{f"Role skill:{chr(10)}{role_skill}" if role_skill else ""}
{f"Contract:{chr(10)}{contract}" if contract else ""}

Respond in JSON:
{{
  "output": "the result of the task",
  "evidence": ["evidence item 1", "evidence item 2"],
  "state_delta": "what changed in the project state",
  "unresolved": ["anything left open"],
  "confidence": "high|medium|low"
}}"""

    prompt = f"""Project: {Path(repo_path).name}

## Project Context
{agent_os}

## Current State
{state}

## Task
{json.dumps(task, indent=2)}

Execute this task and return the result."""

    raw = reason(prompt, system=system, model=Model.SUPER)

    try:
        raw_clean = raw.strip()
        if "```" in raw_clean:
            raw_clean = raw_clean.split("```")[1]
            if raw_clean.startswith("json"):
                raw_clean = raw_clean[4:]
        result = json.loads(raw_clean.strip())
    except Exception:
        result = {"output": raw, "evidence": [], "state_delta": "", "unresolved": [], "confidence": "low"}

    append_event(repo_path, {
        "type": "task_execution",
        "task": task,
        "result": result,
    })

    return result
