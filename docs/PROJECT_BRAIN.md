# Project Brain — Persistent Intelligence

## The Core Insight

Every AI tool you've ever used treats your conversation as the unit of continuity. When the chat ends, so does the context. Tomorrow you start fresh. You re-explain what you're working on. You rebuild the mental model from scratch. You are the integration layer between sessions — a job you should not have to do.

This is not an AI capability failure. It is an architecture failure. The session is the wrong unit.

**The project is the right unit.**

A project is how humans actually track work. It persists across time, tools, and collaborators. It accumulates decisions, evidence, and state. It survives a job change. The conversation is just one interaction in a project's life — a transient channel, not the container.

The Project Brain is the persistent state document for a project. It is the answer to the question: "What does any agent — on any model, in any session — need to know to pick up exactly where we left off?"

---

## The Five Sections

Every Project Brain has exactly five sections. This is not arbitrary — each section answers a distinct question that an agent needs to reason effectively.

### 1. Intent / Goal
**Question:** What is this project trying to achieve?

Not the tasks. Not the current status. The goal — the end state that would mean this project succeeded.

```
Good: "Build a 1,200 sq ft ADU in the backyard that generates $2,800/month in rental income"
Bad:  "Research ADU regulations" (this is a task, not a goal)
```

The goal is the north star for every decision the agent makes. When two paths diverge, the goal breaks the tie.

---

### 2. Current State
**Question:** What is objectively true right now?

This is a machine-readable snapshot of the project's present condition. Not opinions. Not intentions. Facts.

```
Good: "Permit application submitted 2026-09-14. Waiting for city review. Contractor quotes received: 3 of 3. Budget: $180K allocated."
Bad:  "Things are going pretty well, about halfway through"
```

The state must be specific enough that an agent can reason about what to do next without asking clarifying questions.

---

### 3. Decisions / Direction
**Question:** What principles govern this project?

The guiding decisions that have been made — the ones that constrain future choices and prevent relitigating the same questions.

```
Good: "Decision: Use JADU (Junior Accessory Dwelling Unit) classification to stay under permit threshold. Rationale: saves ~$12K and 3 months. Locked 2026-09-01."
Bad:  "We're thinking about going with JADU"
```

Decisions have three properties: what was decided, why, and when it was locked. Without the why, the next agent might reverse a good decision without realizing it was deliberate.

---

### 4. Next Actions
**Question:** What happens next?

Concrete, specific, assignable tasks. Not "research the permit process" — "call Building and Safety Dept (213-482-7070) and ask for permit status on application #2026-ADU-04421."

```
Good:
- Call Building and Safety (213-482-7070) — ask for permit status on #2026-ADU-04421
- Review contractor invoice from Oakwood Construction — due 2026-10-15
- Schedule structural inspection with Carlos Mendez — book through Calendly link

Bad:
- Follow up on permits
- Deal with contractor stuff
```

Actions are the handoff from the Project Brain to the execution layer. A vague action cannot be executed without human intervention — which defeats the purpose.

---

### 5. Memory
**Question:** What should never be forgotten?

Persistent facts, contacts, constraints, and context that are relevant across the life of the project. Things that would take significant effort to reconstruct if lost.

```
Good:
- City processing time: ~6-8 weeks from submission
- Contractor: Oakwood Construction, Carlos Mendez, cmendez@oakwoodcon.com, 661-445-2200
- HOA approval NOT required (standalone lot, confirmed with HOA president 2026-08-20)
- Target rental rate: $2,800/month based on Zillow comps in 90065

Bad: (nothing — this section is often underused)
```

Memory is the accumulation of institutional knowledge. It is what makes the agent smarter the longer the project runs.

---

## Why This Structure

The five sections are designed to answer the questions agents ask in the order they naturally ask them:

```
Agent enters the project
  │
  ├─ "What am I trying to do?" ──────────────→ Intent/Goal
  │
  ├─ "What's the current situation?" ────────→ Current State
  │
  ├─ "What constraints apply?" ──────────────→ Decisions/Direction
  │
  ├─ "What should happen next?" ─────────────→ Next Actions
  │
  └─ "What do I need to remember?" ──────────→ Memory
```

An agent that can answer all five questions can operate autonomously. An agent that cannot answer any of them will ask the user — and the user has to become the integration layer again.

---

## The Portability Property

Project Brains are model-agnostic, session-agnostic, and device-agnostic. This is by design.

A Project Brain written during a session with Claude can be picked up by a session with Gemini, GPT-4, or any future model. The format is plain text — no proprietary embedding, no vendor-specific format, no database that requires a specific runtime.

This is the portability guarantee: your project's intelligence follows you. It does not live in the model's training data. It does not live in a vendor's cloud. It lives in a file you own, under version control you control.

```
Session 1 (Claude, macOS, work) ──┐
Session 2 (Gemini, iOS, park) ────┤──→ Project Brain ←──→ Any future agent
Session 3 (GPT, Windows, travel) ─┘
```

---

## Projects vs Sessions

The distinction is important enough to be explicit.

| Dimension | Session | Project |
|---|---|---|
| Duration | Minutes to hours | Months to years |
| Primary container | Chat history | Project Brain |
| Survives model change | No | Yes |
| Survives employer change | No | Yes |
| Recoverable if lost | Difficult | Yes (git history) |
| Readable by collaborators | No | Yes |
| Machine-readable state | No | Yes |
| Searchable | Sometimes | Always |

Most AI tools today are session-first. Anywhere Stack is project-first. The session is just the most recent interaction with a living project.

---

## The Update Protocol

The Project Brain is a living document. It updates whenever something meaningful happens.

**What triggers a Brain update:**
- A new decision is made
- The current state changes materially
- A new constraint is discovered
- An action is completed or a new one is added
- Important context is uncovered (a contact, a deadline, a fact)

**What does not trigger a Brain update:**
- Exploratory thinking (brainstorming does not become a decision until it is made)
- Reversible tactical moves
- Repeated status updates with no new information

**The key rule:** If a future agent reading the Brain would act differently because of this new information, update it. If not, skip it.

---

## Version Control as Audit Trail

Because each project lives in a repository, the Project Brain has a full version history. Every change is timestamped and attributable. This provides:

- **Rollback:** If the Brain gets corrupted or an agent makes a bad update, the previous state is always recoverable
- **Timeline reconstruction:** Anyone can see how the project evolved — which decisions were made when, which state snapshots existed at which moments
- **Audit compliance:** In enterprise contexts, the version history demonstrates that the agent's actions were authorized and traceable

The `runs/` directory (append-only JSON event log) is the canonical record. The Brain is a projection of `runs/` — it can always be regenerated from the event log if needed.

---

## In the Prototype

In `anywhere_stack_v5.html`, each project card stores a simplified version of the Project Brain:

```json
{
  "goal": "Build ADU for rental income",
  "state": "Permit in progress, 3 contractor quotes received",
  "decision": "Go with JADU classification to minimize permit overhead",
  "actions": [
    "Call Building and Safety for permit status",
    "Review Oakwood invoice",
    "Schedule structural inspection"
  ],
  "memory": "HOA approval not required. Target: $2,800/month rental income."
}
```

When a user submits an intent, the Claude Opus model reads the current Brain, processes the new intent, and returns an updated Brain — all five sections updated where relevant. The UI writes the new Brain back to local state. The project accumulates intelligence with every interaction.
