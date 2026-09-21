# Example Project

## Mission
Demonstrate the Anywhere Stack repo module structure. A working example any agent can enter and act on.

## Phase
EXAMPLE — for reference and testing only

## Roles
- **Project Manager**: reconcile state, surface blockers, delegate to builder
- **Builder**: execute bounded tasks, record evidence

## Invariants
- Record all decisions with evidence in `decisions.md`
- Never close an issue without a recorded resolution
- Do not modify this `agent-os.md` without human approval

## Acceptance Criteria
- `state.md` reflects current project phase
- All open issues have an owner or are escalated
- `brief.md` is current (regenerated each heartbeat)

## Source of Truth
- This file: mission and contracts
- `state.md`: current accepted state
- `decisions.md`: decision log
- `runs/`: canonical event history

## Next Action
Run `anywhere heartbeat example-project` to initialize state projections.
