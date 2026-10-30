"""Role relation graph — typed edges between agent roles.

Represents the coordination topology as data (Yohei's relation-behavior primitive).
Each Relation is a typed edge: source_role --rel_type--> target_role, triggered
by a specific event type. Behaviors fire on edge type, not on hardcoded call graphs.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Relation:
    source: str
    target: str
    rel_type: str
    on_event: str
    description: str = ""
    metadata: dict = field(default_factory=dict)


# Canonical role topology — the "physics" of Anywhere Stack coordination
ROLE_RELATIONS: list[Relation] = [
    Relation(
        source="cos",
        target="pm",
        rel_type="dispatches_to",
        on_event="project.needs_triage",
        description="CoS dispatches PM when a project needs attention",
    ),
    Relation(
        source="pm",
        target="builder",
        rel_type="delegates_to",
        on_event="task.ready_for_builder",
        description="PM delegates a bounded task to Builder",
    ),
    Relation(
        source="builder",
        target="pm",
        rel_type="reports_to",
        on_event="task.completed",
        description="Builder reports completion back to PM",
    ),
    Relation(
        source="builder",
        target="pm",
        rel_type="reports_failure_to",
        on_event="task.failed",
        description="Builder surfaces failures to PM for re-triage",
    ),
    Relation(
        source="cos",
        target="human",
        rel_type="escalates_to",
        on_event="escalation.required",
        description="CoS escalates to human when judgment is needed",
    ),
    Relation(
        source="regimes",
        target="builder",
        rel_type="patches",
        on_event="regime.patch_proposed",
        description="Regimes loop proposes behavioral patches for validation",
    ),
]


def relations_for(
    source: str | None = None,
    target: str | None = None,
    rel_type: str | None = None,
) -> list[Relation]:
    """Query relations by source, target, or rel_type."""
    result = list(ROLE_RELATIONS)
    if source:
        result = [r for r in result if r.source == source]
    if target:
        result = [r for r in result if r.target == target]
    if rel_type:
        result = [r for r in result if r.rel_type == rel_type]
    return result


def topology_summary() -> str:
    lines = ["Role Topology (typed graph edges):"]
    for r in ROLE_RELATIONS:
        lines.append(f"  {r.source:8s} --[{r.rel_type}]--> {r.target:8s}  (on: {r.on_event})")
    return "\n".join(lines)
