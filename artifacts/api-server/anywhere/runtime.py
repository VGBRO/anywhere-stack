"""Event-driven behavior runtime — Layer 3 of the Yohei/ActiveGraph pattern.

Three layers in this system:
  Layer 1: Event log    — append-only records in <project>/runs/ + .lineage.sqlite
  Layer 2: Projections  — state.md, brief.md, query_lineage() — derived from Layer 1
  Layer 3: Behaviors    — reactive functions registered here, fired by event type

No component instructs another directly. Coordination happens through the shared
event queue. A behavior emits events; those events fire other behaviors.
"""

from __future__ import annotations

import traceback
from typing import Callable

# event_type -> [behavior_fn]
_REGISTRY: dict[str, list[Callable]] = {}


def on(event_type: str) -> Callable:
    """Register a behavior that fires when event_type is emitted."""
    def decorator(fn: Callable) -> Callable:
        _REGISTRY.setdefault(event_type, []).append(fn)
        return fn
    return decorator


def dispatch(event: dict, context: dict) -> list[dict]:
    """Fire all behaviors registered for event["type"]. Return emitted events."""
    event_type = event.get("type", "")
    emitted: list[dict] = []
    for behavior_fn in _REGISTRY.get(event_type, []):
        try:
            result = behavior_fn(event, context)
            if result is None:
                continue
            if isinstance(result, dict):
                emitted.append(result)
            else:
                emitted.extend(result)
        except Exception as e:
            emitted.append({
                "type": "behavior.failed",
                "behavior": getattr(behavior_fn, "__name__", str(behavior_fn)),
                "triggering_event_type": event_type,
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
    return emitted


def run_until_idle(
    initial_events: list[dict],
    context: dict,
    max_iterations: int = 50,
    on_event: Callable[[dict], None] | None = None,
) -> list[dict]:
    """Process the event queue until no new events are emitted (or max_iterations)."""
    queue = list(initial_events)
    all_events: list[dict] = []
    iterations = 0
    while queue and iterations < max_iterations:
        event = queue.pop(0)
        all_events.append(event)
        if on_event:
            on_event(event)
        new_events = dispatch(event, context)
        queue.extend(new_events)
        iterations += 1
    return all_events


def registered_behaviors() -> dict[str, list[str]]:
    """Return {event_type: [fn_name, ...]} — useful for introspection."""
    return {k: [fn.__name__ for fn in v] for k, v in _REGISTRY.items()}
