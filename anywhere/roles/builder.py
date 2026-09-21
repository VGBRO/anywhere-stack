"""Builder role — bounded task execution within a project repo."""

import json
from pathlib import Path
from anywhere.client import reason, Model
from anywhere.state.canonical import append_event, parse_json, read_agent_os, read_state


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

If the task produces a file (a document, README, plan, analysis), include the FULL file content in the "file_output" field along with the relative path in "file_path". The system will write it to disk — you do not need to simulate writing.

Respond in JSON:
{{
  "output": "one-sentence summary of what was done",
  "file_path": "relative/path/to/file.md or null",
  "file_output": "full file content to write, or null",
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

    result = parse_json(raw)
    if not result:
        result = {"output": (raw or "")[:500], "evidence": [], "state_delta": "", "unresolved": [], "confidence": "low"}

    # Materialize file output if the Builder produced file content
    if result.get("file_path") and result.get("file_output"):
        out_path = Path(repo_path) / result["file_path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result["file_output"])
        result["evidence"] = result.get("evidence", []) + [f"Written: {result['file_path']}"]

    append_event(repo_path, {
        "type": "task_execution",
        "task": task,
        "result": result,
    })

    return result
