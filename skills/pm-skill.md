# Skill: Project Manager Heartbeat

## Purpose
Project-level state reconciliation. Sequence work, surface blockers, delegate to builders.

## Procedure

### Step 1 — Load Project State
Read in this order:
1. `agent-os.md` — mission, contracts, roles, invariants
2. `state.md` — current accepted state
3. `decisions.md` — recent decisions
4. `issues/` — open work queue (filter: status != done)
5. `runs/` — last 5 heartbeat events

### Step 2 — Reconcile State
Ask:
- Does the current state match the project's objective and phase?
- Are there blockers preventing progress?
- Are there issues with no assigned owner?
- Is any work stale (not updated in > 3 days)?

### Step 3 — Prioritize
Rank open issues:
1. Blocking issues (nothing else can proceed)
2. High-priority, assigned issues
3. High-priority, unassigned issues
4. Medium-priority issues
5. Low-priority / parking lot

### Step 4 — Act
- Select the single highest-priority issue
- If it can be delegated to a builder → dispatch task packet
- If it requires human judgment → escalate with clear framing
- If it is a blocker with no path forward → mark health: red, escalate

### Step 5 — Record and Exit
- Append PM heartbeat event to canonical history
- Regenerate `state.md` and `brief.md`
- Exit. Do not implement work directly.
