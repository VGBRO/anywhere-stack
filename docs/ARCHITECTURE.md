# Architecture — Anywhere Stack

## The Core Problem

Most AI tools give you one of two things:

**Personal agents** (Muse, Instinct, Grok) know you — your preferences, your projects, your history. But they stop at the office door. The moment you walk into a corporate environment, they can't touch work systems. They're useless for the tasks that matter most during your day.

**Enterprise agents** (Copilot, Salesforce Agentforce) can access work systems. But they don't know you. They have no memory of your decisions, your communication style, or what you were working on last week. You start from zero with every interaction.

The gap between them is paid by you, in friction, every single day — manually carrying context between your life and your work.

**Anywhere Stack bridges that gap.**

---

## Design Principles

### 1. The project is the durable unit — not the session

Every existing AI tool treats the conversation as the unit of continuity. When the session ends, continuity is lost. You re-explain context. You rebuild state. The model never learns.

Anywhere Stack inverts this. State, decisions, evidence, and memory live in the **Project Brain** — a structured, versioned document that persists across sessions, devices, models, and employers. The conversation is ephemeral. The project is permanent.

```
Conventional model:           Anywhere Stack:
Session → context lost        Project Brain → persists forever
Re-explain every time         Any agent picks up where the last left off
Tied to one model             Swap models freely; state is model-agnostic
```

### 2. Your intelligence travels with you

When you change jobs, you leave behind the enterprise AI. You don't leave behind yourself. Anywhere Stack stores your intelligence — your decisions, your communication style, your domain knowledge — in a portable Project Brain that is yours, not the company's.

### 3. FirmOS makes it enterprise-safe

The objection to personal agents in the workplace is trust. IT and CISO cannot allow an uncontrolled personal AI to access corporate systems. FirmOS solves this with two security layers (see [FIRMOS.md](FIRMOS.md)).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOU                                       │
│           (phone, park, office, Slack, anywhere)                │
└─────────────────────────────┬───────────────────────────────────┘
                              │ natural language intent
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTENT INBOX                                  │
│  • Captures intent in any context                               │
│  • Works offline — queues locally when no connectivity          │
│  • Syncs to Nemotron pipeline when back online                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ online                        │ offline
              ▼                               ▼
┌─────────────────────────┐   ┌───────────────────────────────────┐
│   NEMOTRON NANO         │   │   LOCAL QUEUE                      │
│   Intent Router         │   │   (keyword match + store)          │
│   ~100ms, cheap         │   │   Ollama/nemotron-mini if avail.   │
│   Routes to project     │   │   Flushes to Nemotron on sync     │
└────────────┬────────────┘   └───────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 NEMOTRON ULTRA                                   │
│                 Chief of Staff                                   │
│  • Deep reasoning over the full project portfolio               │
│  • Generates structured Project Brain updates                   │
│  • Dispatches work to Project Managers reactively               │
│  • Escalates to human when judgment is required                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │ event-driven dispatch
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PROJECT BRAIN                                    │
│  ┌──────────┬───────────┬────────────┬──────────┬────────────┐  │
│  │  Intent  │   State   │ Decisions  │ Actions  │  Memory   │  │
│  └──────────┴───────────┴────────────┴──────────┴────────────┘  │
│  Versioned, portable, readable by any agent or collaborator     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIRM OS                                       │
│  ┌────────────────────────┐  ┌─────────────────────────────┐   │
│  │      IN-BAND           │  │        OUT-OF-BAND           │   │
│  │  Evals · Test harness  │  │  Gateway · Proxy · Firewall  │   │
│  │  Internal firewall     │  │  Audit log · Runtime monitor │   │
│  └────────────────────────┘  └─────────────────────────────┘   │
│                    Trust boundary                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │ governed access
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              CORPORATE SYSTEMS                                   │
│      Salesforce · Slack · GitHub · Any connected tool           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Nemotron Model Routing Strategy

Not all reasoning is equal. Calling the largest model for every operation wastes money and adds latency. Anywhere Stack routes each call to the right model tier.

```
Intent arrives
      │
      ▼
  NANO (30B)           ← Is this intent for an existing project or new?
  ~100ms, cheap           Which project does it belong to?
      │                   Confidence: 0.0–1.0
      │
      ▼
  ULTRA (550B)         ← Generate the full Project Brain update
  ~2s, powerful           Understand context, decisions, history
                          Return structured JSON: goal / state /
                          decisions / actions / memory
```

**Why this split?**

Routing is a pattern-matching problem. A 30B model handles it well and costs ~1/18th of the 550B model. The 550B model is reserved for the task that actually requires deep reasoning: understanding what changed, what it means for the project, and what should happen next.

This is the same principle as a human organization: a junior analyst triages the inbox (fast, cheap), a senior executive synthesizes the implications (slow, expensive).

| Model | Tier | Used For | Why |
|---|---|---|---|
| `Nemotron-3-Ultra-550b-a55b` | 550B | Chief of Staff reasoning | Deep portfolio analysis, brain updates |
| `nemotron-3-super-120b-a12b` | 120B | Project Manager triage | Task planning, sequencing |
| `NVIDIA-Nemotron-3-Nano-30B-A3B` | 30B | Intent routing | Fast classification (~100ms) |
| `Nemotron-3_5-Lightning` | Fast | High-frequency calls | Projection generation, formatting |
| `Hermes-4-405B` | 405B | Tool calling | Agentic loops with structured tool use |

---

## Offline-First Design

The name "Anywhere Stack" is literal. The system must work when you're at the park, on a plane, or in a dead zone.

```
OFFLINE                          ONLINE
   │                                │
   ├─ Keyword intent capture        ├─ Nemotron NANO routing
   ├─ Local project match           ├─ Nemotron ULTRA CoS reasoning
   ├─ Queue to LocalQueue[]         ├─ Full Project Brain update
   └─ Bira auto-approve             └─ Sync flush of offline queue
        (no network needed)
```

**The Bira moment** is the flagship demo of this design: a user at the park says "go ahead and plan my ADU" while spending time with their dog Bira. The system creates the project locally, queues the research work, and responds immediately — no connectivity required. When they reconnect, the full Nemotron pipeline processes the queue and the Project Brain is fully populated.

The offline layer has three fallback tiers:
1. **Ollama + nemotron-mini** — on-device inference, full classification
2. **Keyword matching** — zero-dependency fallback
3. **Queue only** — capture and defer, no classification

---

## Event-Driven Coordination

The CoS does not call the PM directly. It emits events. The runtime fires the PM behavior reactively when a matching event arrives. No component instructs another — coordination happens through the shared event queue.

```python
# CoS emits an event
emit({
    "type": "project.needs_triage",
    "project": "india-ai-infrastructure",
    "urgency": "high"
})

# Runtime fires PM behavior reactively
@on("project.needs_triage")
def pm_triage(event, context):
    ...
```

This design is based on the **Yohei/ActiveGraph** coordination model. Benefits:
- Components are independently testable
- New behaviors can be added without modifying existing ones
- The event log is the canonical audit trail
- Any component can be replaced without changing the system topology

---

## Repository as Canonical State

Every project in Anywhere Stack is a repository. The repository carries all continuity.

```
project-repo/
├── agent-os.md     ← mission, contracts, role definitions (entry point for any agent)
├── state.md        ← machine-readable current state (regenerated from runs/)
├── brief.md        ← human-readable summary (regenerated from runs/)
├── decisions.md    ← append-only decision log with provenance
├── issues/         ← work queue: open → assigned → done
├── runs/           ← canonical event history (append-only JSON)
├── claims/         ← proposed claims awaiting verification
└── memory/         ← durable cross-session memory
```

**The invariant:** `runs/` is append-only and never rewritten. `state.md` and `brief.md` are projections — they can be regenerated at any time from `runs/`. If projections become stale, the record beneath them cannot.

Any agent — on any model, in any session — can enter a project by reading `agent-os.md` + `state.md` and continue exactly where the last agent left off.

---

## The Instruction Stack

Agent behavior is composed from four layers, not one large prompt:

```
Layer 4: Task context        ← current objective, files, constraints (narrowest)
Layer 3: Project contract    ← mission, invariants, acceptance criteria
Layer 2: Role skill          ← procedure for this role (reusable across projects)
Layer 1: Global rules        ← invariants for all agents (widest)
```

The same role skill works across any project. Project-specific truth stays local. A Builder role executing a task for "India AI Infrastructure" uses the same Builder skill as one executing for "Telugu Thriller" — only the project contract changes.

This composability keeps the system maintainable as it scales across many projects and many role types.
