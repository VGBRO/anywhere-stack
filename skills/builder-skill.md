# Skill: Builder Task Execution

## Purpose
Execute a bounded task. Implement, record evidence, exit.

## Procedure

### Step 1 — Load Context
Read:
1. Task packet (objective, constraints, acceptance criteria, authority)
2. `agent-os.md` — project invariants and boundaries
3. `state.md` — current accepted state

### Step 2 — Verify Authority
Before acting, confirm:
- The task is within the stated authority boundary
- The task does not alter acceptance criteria or project invariants
- No external actions are required beyond what was pre-authorized

If any of these fail → escalate to PM, do not proceed.

### Step 3 — Execute
- Do the work described in the task packet
- Record evidence as you go (what you observed, what you changed, what you tested)
- Stay within scope — if something unexpected requires out-of-scope action, stop and record it

### Step 4 — Verify Result
Check the result against the acceptance criteria in the task packet:
- Does it meet the criteria? → mark complete with confidence level
- Does it partially meet them? → record what is done and what remains
- Does it fail? → record the failure with diagnosis

### Step 5 — Record and Exit
- Append task execution event to canonical history
- State delta: what changed, what is new, what is still open
- Exit. Leave the repo in a state any agent could pick up.

## Quality Bar
- Confidence: high → meets criteria, evidence is clear
- Confidence: medium → mostly meets criteria, some uncertainty
- Confidence: low → partial or uncertain — escalate before marking done
