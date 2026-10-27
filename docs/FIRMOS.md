# FirmOS — The Trust Layer

## The Problem It Solves

Every knowledge worker today faces the same invisible wall.

You have a personal AI agent. It knows your work style, your decisions, your projects. It's genuinely useful. But the moment you try to use it at work — connecting it to Salesforce, Slack, your company's GitHub — IT security shuts it down. The corporate firewall doesn't trust your personal agent. The CISO has no visibility into what it accesses, what it writes, or where data goes.

So you end up with two disconnected systems:
- Your personal agent (powerful, knows you, can't touch work systems)
- Enterprise AI tools (connected to work systems, doesn't know you, resets every session)

FirmOS is the layer that makes both work together. It is not a product. It is an operating protocol.

---

## The Passport + Visa Metaphor

Think of it this way:

```
                    YOU OWN
                    ┌─────────────────────────┐
                    │      YOUR PASSPORT       │
                    │  Identity + Intelligence │
                    │  Skills, decisions,      │
                    │  memory, working style   │
                    └─────────────────────────┘
                             │
                             │ apply for a visa
                             ▼
                    COMPANY ISSUES
                    ┌─────────────────────────┐
                    │       YOUR VISA          │
                    │  Governed access to      │
                    │  corporate systems       │
                    │  Scoped to role + need   │
                    └─────────────────────────┘
```

**Your passport is yours.** It travels with you when you change jobs. It holds your intelligence, your accumulated context, your decisions. The company never owns it.

**The visa is the company's.** It grants your personal agent access to specific corporate systems, under defined constraints, for a scoped purpose. The company can revoke it. The company audits what it accesses.

This is not a new idea — it's how international travel has worked for 100 years. FirmOS applies it to AI agent access.

---

## Two Security Layers

FirmOS implements security in two phases: before runtime and at runtime.

### In-Band Security (Before Runtime)

Governance that runs during development and agent configuration — before any user interaction happens.

```
┌──────────────────────────────────────────────────────┐
│                   IN-BAND                            │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │   Evals      │    │  Test Harness│               │
│  │  Does the    │    │  Does the    │               │
│  │  agent behave│    │  agent do    │               │
│  │  correctly?  │    │  what it's   │               │
│  │              │    │  supposed to │               │
│  │  Red team.   │    │  under       │               │
│  │  Adversarial │    │  adversarial │               │
│  │  prompts.    │    │  inputs?     │               │
│  └──────────────┘    └──────────────┘               │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │            Internal Firewall                  │   │
│  │  Defines what the agent CAN access at all.   │   │
│  │  Not per-request — structural constraint.    │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**What in-band catches:**
- Prompt injection attacks
- Scope creep (agent doing things outside its defined purpose)
- Behavioral drift over time
- Logic errors in agent reasoning

**When it runs:**
- During agent development
- Before deployment
- On each version update

---

### Out-of-Band Security (At Runtime)

Governance that monitors and constrains the agent while it is actively running — every call, every action.

```
┌──────────────────────────────────────────────────────┐
│                 OUT-OF-BAND                          │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │   Gateway    │    │    Proxy     │               │
│  │  Every API   │    │  All traffic │               │
│  │  call routes │    │  routes      │               │
│  │  through one │    │  through     │               │
│  │  choke point │    │  observable  │               │
│  │              │    │  layer       │               │
│  └──────────────┘    └──────────────┘               │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │   Firewall   │    │  Audit Log   │               │
│  │  Real-time   │    │  Every       │               │
│  │  blocking    │    │  action is   │               │
│  │  of          │    │  immutably   │               │
│  │  disallowed  │    │  recorded    │               │
│  │  actions     │    │              │               │
│  └──────────────┘    └──────────────┘               │
└──────────────────────────────────────────────────────┘
```

**What out-of-band catches:**
- Anomalous behavior that passed evals but emerges at runtime
- Attempts to access out-of-scope resources
- Unusual data volumes or access patterns
- Compliance violations that only appear in production conditions

**What it provides IT/CISO:**
- Complete audit trail of every agent action
- Real-time visibility into what the agent is doing
- Ability to block, throttle, or shut down without code changes
- Evidence for security review cycles

---

## CISO Compliance Story

The reason most enterprises cannot adopt personal AI agents is not technical. It is organizational. The CISO has no answer to these questions:

1. What systems can this agent access?
2. What data does it read and write?
3. Can we audit what it did?
4. Can we shut it down if something goes wrong?
5. Who owns the agent?

FirmOS answers all five:

| CISO Question | FirmOS Answer |
|---|---|
| What systems can it access? | Defined at deployment by the internal firewall (in-band). Scoped, explicit, reviewable. |
| What data does it read/write? | Every call goes through the gateway and proxy (out-of-band). Observable in real time. |
| Can we audit it? | Yes. The audit log is immutable and complete. Every action, every call, every decision. |
| Can we shut it down? | Yes. The gateway is a choke point. Revoke the visa and the agent loses access immediately. |
| Who owns the agent? | Clear separation: the employee owns the passport (personal intelligence), the company owns the visa (access grant). |

This is why we call it a visa system. A visa is not a gift — it is a governed permission with clear conditions, audit trails, and revocation authority. That is exactly what the enterprise needs from personal AI.

---

## What FirmOS Is Not

**Not a product you install.** FirmOS is an architectural protocol. It describes the trust layer a personal AI agent stack should implement to operate inside enterprise boundaries.

**Not a content filter.** FirmOS does not censor or modify agent outputs. It governs access (what can the agent reach?) not content (what can the agent say?).

**Not owned by the enterprise.** The personal intelligence layer — the Project Brain, the memory, the skills — stays with the employee. FirmOS only governs the interface between personal AI and corporate systems.

**Not a replacement for enterprise AI.** Enterprise tools (Copilot, Agentforce) remain the company's AI surface. FirmOS allows the employee's personal agent to augment those tools — not compete with them.

---

## The Credential and Storage Boundary

One of the most important properties of a FirmOS implementation is the **data residency guarantee**.

```
┌─────────────────────────────────────────────────────────┐
│                  PERSONAL SPACE                         │
│  Project Brain · Skills · Decisions · Memory           │
│  Stored locally or in employee-owned cloud              │
│  Company has NO access to this layer                   │
└─────────────────────────────────────────────────────────┘
                           │
                    FirmOS Trust Boundary
                           │
┌─────────────────────────────────────────────────────────┐
│                  CORPORATE SPACE                        │
│  Salesforce · Slack · GitHub · Corporate data          │
│  Agent accesses with corporate credentials              │
│  Company has full visibility and control               │
└─────────────────────────────────────────────────────────┘
```

**Corporate data does not flow into the personal space by default.** When the agent reads a Salesforce record, it uses that data to reason — it does not copy it into the employee's personal Project Brain. This is the boundary that makes the system legally and organizationally acceptable.

The employee brings their intelligence to the work. They do not take the company's data home.

---

## Practical Implementation (Today)

FirmOS is not a fully built product. In the current prototype:

- **In-band:** The agent prompts are written with explicit scope definitions. Bira auto-approve only fires for personal context (backyard, ADU, off-hours). Work-context intents require more deliberate confirmation.

- **Out-of-band:** All API calls go through a single FastAPI server (`api.py`). Every call is logged. The server acts as the gateway — a single choke point for all Nemotron traffic.

- **Audit log:** `runs/` in each project repository is append-only. No action can be silently erased.

- **Revocation:** The `NEBIUS_API_KEY` environment variable is the effective kill switch for the reasoning layer. Removing it from the deployment immediately terminates all AI capability.

The full FirmOS vision — enterprise gateway integration, SCIM-based credential management, real-time CISO dashboard — is the roadmap beyond the hackathon prototype.
