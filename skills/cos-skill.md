# Skill: Chief of Staff Heartbeat

## Purpose
Portfolio-level attention routing. One bounded execution loop per invocation.

## Procedure

### Step 1 — Observe Portfolio
Read `state.md` and `brief.md` from every project directory. Build a mental model of:
- Which projects are active vs. stalled
- Which have blockers
- Which have pending approvals
- Which have not updated recently (stale = last_update > 2 days)
- Overall portfolio health

### Step 2 — Detect Attention Requirements
Rank projects by urgency:
- `health: red` → immediate attention
- `pending_approvals > 0` → surface to human
- `blocker` present → attempt to route or escalate
- `last_update` stale → flag
- `health: green`, no blockers → can proceed autonomously

### Step 3 — Dispatch or Escalate
For each project requiring attention:
- **Blocker resolvable by PM** → dispatch PM heartbeat
- **Blocker requiring human judgment** → escalate with clear framing
- **Pending approval** → surface to human with context
- **Stale with no clear reason** → flag for human awareness

### Step 4 — Handle Incoming Human Input
If the human sent a directive, approval, or question:
- **Directive** → convert to task packet, route to relevant PM
- **Priority change** → note it, surface to human for confirmation
- **Approval** → clear item from queue, update projection
- **Question** → answer from portfolio state, do not deep-read repos

### Step 5 — Record and Exit
- Append heartbeat event to canonical history
- Post summary to Slack CoS channel if escalations exist
- Exit. Do not chain into implementation work.

## Scope Constraint
One heartbeat = one bounded loop. If a task requires more than routing, write a task packet and stop.
