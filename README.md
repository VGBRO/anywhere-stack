# Anywhere Stack

**A repo-centric modular agent stack powered by NVIDIA Nemotron on Nebius.**

> The hardware gets you online. The control plane makes work portable.

Built for the **NVIDIA × Nebius Global AI Hackathon** — Personal AI track.

---

## What It Is

Anywhere Stack is a personal AI operating system where the **durable unit is the project repository**, not the model, agent, tool, or chat session.

The conventional AI interaction model keeps context inside the session — when the session ends, continuity is lost. Anywhere Stack inverts this:

- **Durable state lives in the repository** — versioned, inspectable, portable across models and sessions
- **Agents are replaceable execution** — swap Nemotron for any model; the project keeps running
- **Any agent can resume** — enter any project, read `agent-os.md` + `state.md`, and continue where the last agent left off

You talk to it from your phone via Slack. It manages your projects, routes work, and keeps everything moving — from anywhere, hands free.

---

## Architecture

```
You (Slack on mobile)
        ↕
Chief of Staff          ← portfolio view, routing, escalation
        ↕
Project Managers        ← per-project state, task sequencing
        ↕
Builders                ← bounded task execution, evidence recording
        ↕
Project Repositories    ← canonical history + derived projections
```

Every component is a **bounded heartbeat**: wake → inspect → act → record → exit. The repository carries continuity between heartbeats, not the model's context.

---

## NVIDIA Nemotron + Nebius Token Factory

All inference runs on **Nebius Token Factory** using NVIDIA open source models:

| Model | Used For |
|-------|----------|
| `nvidia/Nemotron-3-Ultra-550b-a55b` | Chief of Staff reasoning, deep portfolio analysis |
| `nvidia/nemotron-3-super-120b-a12b` | Project Manager triage, task planning |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | Fast routing, message classification |
| `nvidia/Nemotron-3_5-Lightning` | High-frequency calls, projection generation |

The layered model usage keeps the system responsive and cost-efficient: Ultra only fires on deep reasoning (CoS heartbeat); Nano handles the frequent, fast calls.

---

## Repo Module Structure

Every project is a self-contained repo with a canonical layout:

```
my-project/
├── agent-os.md       ← project brief: mission, contracts, roles (entry point for any agent)
├── state.md          ← machine-readable projection: current phase, health, next action
├── brief.md          ← human-readable projection: current status summary
├── decisions.md      ← decision log with provenance (append only)
├── issues/           ← work queue: open, assigned, blocked, done
├── runs/             ← canonical event history (append-only JSON events)
├── claims/           ← proposed claims awaiting verification
├── evidence/         ← sources, test results, observations
├── contracts/        ← schemas, invariants, acceptance criteria
└── memory/           ← durable cross-session memory
```

---

## Instruction Stack

Agent behavior is composed from four distinct layers, not one large prompt:

```
4. Task context       — current objective, files, constraints (narrowest)
3. Project contract   — mission, invariants, acceptance criteria (per-project)
2. Role skill         — procedure for this role (reusable across projects)
1. Global rules       — invariants for all agents (widest)
```

Same role skill works across any project. Project-specific truth stays local.

---

## Setup

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Nebius Token Factory API key ([tokenfactory.nebius.com](https://tokenfactory.nebius.com))
- Slack app with Socket Mode enabled ([api.slack.com/apps](https://api.slack.com/apps))

### Install

```bash
git clone https://github.com/VGBRO/anywhere-stack.git
cd anywhere-stack
bash scripts/bootstrap.sh
```

### Configure

```bash
cp .env.example .env
# Edit .env — add NEBIUS_API_KEY and Slack tokens
```

### Verify

```bash
anywhere test-nebius           # Test Nebius + list Nemotron models
anywhere heartbeat example-project  # Run first heartbeat
anywhere status                # Show portfolio health
```

### Start Slack Listener

```bash
anywhere slack
```

---

## Usage

### CLI

```bash
# Portfolio heartbeat (Chief of Staff)
anywhere heartbeat

# Project heartbeat (Project Manager)
anywhere heartbeat my-project

# Portfolio status
anywhere status

# Project status
anywhere status my-project

# Initialize a new project
anywhere init my-project --mission "Build a customer onboarding automation"
```

### Slack

Once the listener is running, mention the bot or send messages in your CoS channel:

```
@anywhere-stack status
@anywhere-stack status my-project
heartbeat                              # triggers CoS heartbeat
Ship the onboarding flow for Project X # directive — routed to PM
```

---

## How a Heartbeat Works

```
1. Wake     — triggered by cron, Slack message, or CLI
2. Inspect  — read project state (agent-os.md, state.md, issues/, runs/)
3. Act      — Nemotron reasons about current state, determines next action
4. Record   — append structured event to runs/ (canonical history)
5. Exit     — regenerate state.md + brief.md, leave repo pickupable
```

The project state carries continuity. The next heartbeat picks up exactly where this one left off — regardless of which model runs it.

---

## Durable Continuity

The core property: **any agent can resume any project with minimal context loading**.

```
event history → projection logic → current state
```

- `runs/*.json` — canonical history (append-only, never rewritten)
- `state.md` — machine projection (regenerated, always traceable)
- `brief.md` — human projection (regenerated, always traceable)

A projection can become stale. The record beneath it cannot.

---

## Adding Your Own Projects

```bash
anywhere init my-project --mission "What this project is for"
```

Then edit `projects/my-project/agent-os.md` to add your contracts, invariants, and acceptance criteria. Run a heartbeat to generate initial state projections.

---

## Hackathon

Built for the **NVIDIA × Nebius Global AI Hackathon** (Personal AI track).  
Submission period: August 26 – October 30, 2026.

**What was built during the submission period:**
- Full Nebius Token Factory integration with all four Nemotron models
- Model routing strategy (Ultra/Super/Nano/Lightning by call type)
- Slack interface with directive routing, status queries, and heartbeat triggers
- CLI (`anywhere`) for all operations
- Canonical repo module structure (agent-os.md, runs/, issues/, claims/, evidence/)
- Example project with working heartbeat
- Bootstrap script for one-command setup

---

## License

MIT — see [LICENSE](LICENSE)
