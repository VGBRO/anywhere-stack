"""Skill runner — load a skill package and execute it with tools."""

from __future__ import annotations

import json
from pathlib import Path
from anywhere.client import execute_with_tools, Model
from anywhere.tools.registry import TOOL_SCHEMAS, make_executor


_SKILLS_DIR = Path(__file__).parent


def list_skills() -> list[str]:
    return [d.name for d in _SKILLS_DIR.iterdir() if d.is_dir() and (d / "manifest.json").exists()]


def load_skill(skill_name: str) -> dict:
    skill_dir = _SKILLS_DIR / skill_name
    if not skill_dir.exists():
        raise ValueError(f"Skill '{skill_name}' not found. Available: {list_skills()}")
    manifest = json.loads((skill_dir / "manifest.json").read_text())
    instructions = (skill_dir / "instructions.md").read_text()
    return {"manifest": manifest, "instructions": instructions}


def run_skill(skill_name: str, prompt: str, repo_path: str = ".") -> str:
    """
    Run a named skill against a repo.
    Loads manifest + instructions, filters tools to what the skill declares, calls execute_with_tools().
    """
    skill = load_skill(skill_name)
    manifest = skill["manifest"]

    allowed = set(manifest.get("tools", []))
    tools = [t for t in TOOL_SCHEMAS if t["function"]["name"] in allowed] if allowed else TOOL_SCHEMAS

    model_name = manifest.get("model", "HERMES")
    try:
        model = Model[model_name]
    except KeyError:
        model = Model.HERMES

    executor = make_executor(repo_path)

    return execute_with_tools(
        prompt=prompt,
        tools=tools,
        executor=executor,
        system=skill["instructions"],
        model=model,
    )
