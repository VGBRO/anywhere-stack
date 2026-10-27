"""Builder role — bounded task execution within a project repo."""

import json
import traceback
from pathlib import Path
from anywhere.client import execute_with_tools, Model
from anywhere.state.canonical import append_event, read_agent_os, read_state
from anywhere.tools.registry import TOOL_SCHEMAS, make_executor


def execute_task(repo_path: str, task: dict) -> dict:
    """
    Execute a bounded task within a project repo using Hermes-4 + real tools.
    Returns a result dict compatible with the PM's expectations.
    """
    agent_os = read_agent_os(repo_path)
    state = read_state(repo_path)

    skill_path = Path(__file__).parent.parent.parent / "skills" / "builder-skill.md"
    role_skill = skill_path.read_text() if skill_path.exists() else ""

    system = f"""You are a Builder executing a bounded task in a project repo.
You have tools — USE THEM to do the work, not describe it.

Rules:
- Use list_files / read_file to understand the project before acting
- Use write_file to create or update files — never output file content as plain text
- Use close_issue when the task maps to an open issue and is complete
- Use create_issue to record follow-up work discovered during execution
- When done, respond with a single plain-text sentence summarising what you did

Your authority: implement what is asked. Do not alter acceptance criteria or project invariants.
{f"{chr(10)}Role skill:{chr(10)}{role_skill}" if role_skill else ""}"""

    prompt = f"""Project: {Path(repo_path).name}

## Project Context
{agent_os}

## Current State
{state}

## Task
{json.dumps(task, indent=2)}

Execute this task using your tools. When complete, write one sentence summarising what you did."""

    # Wrap executor to capture tool calls as evidence
    evidence: list[str] = []
    raw_executor = make_executor(repo_path)

    def tracked_executor(name: str, args: dict) -> str:
        result = raw_executor(name, args)
        summary = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
        evidence.append(f"{name}({summary})")
        return result

    try:
        final_text = execute_with_tools(
            prompt=prompt,
            tools=TOOL_SCHEMAS,
            executor=tracked_executor,
            system=system,
            model=Model.HERMES,
        )
    except Exception as e:
        # Failure is a first-class event — not a swallowed exception
        append_event(repo_path, {
            "type": "task_failure",
            "task_objective": task.get("objective", ""),
            "reason": str(e),
            "traceback": traceback.format_exc(),
        })
        return {
            "output": f"Task failed: {e}",
            "evidence": evidence,
            "state_delta": "failed",
            "unresolved": [str(e)],
            "confidence": "low",
            "failure": str(e),
        }

    # Confidence: high if files were written or issues closed, medium if any tools ran, low otherwise
    tools_used = [e.split("(")[0] for e in evidence]
    if any(t in tools_used for t in ("write_file", "close_issue")):
        confidence = "high"
    elif evidence:
        confidence = "medium"
    else:
        confidence = "low"

    result = {
        "output": final_text,
        "evidence": evidence,
        "state_delta": "Tools used: " + ", ".join(dict.fromkeys(tools_used)) if tools_used else "No tools called",
        "unresolved": [],
        "confidence": confidence,
    }

    append_event(repo_path, {
        "type": "task_execution",
        "task": task,
        "result": {"output": result["output"], "confidence": confidence, "state_delta": result["state_delta"]},
        "tools_called": evidence,
    })

    return result
