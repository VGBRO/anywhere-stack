# Anywhere Stack

**The personal AI that travels with you — including to work.**

> "For the first time in history, billions of people have personal AI Agents. And yet — there is still a wall. The moment you walk into work, you leave it at the front door. Anywhere Stack tears that wall down."

Built for the **NVIDIA × Nebius Global AI Hackathon 2026** — Personal AI track.

---

## The Problem

Personal agents (Muse, Grok, Instinct) stop at the office door. Enterprise agents (Copilot, Salesforce Agentforce) don't know you. You are stuck manually carrying context between your life and your work — every day.

**Anywhere Stack is the first personal agent built to cross that line.**

---

## What It Is

Anywhere Stack is a personal AI operating system with two core primitives:

**1. Project Brain** — persistent, structured memory across every context. Not a chat history. A living document with five sections per project: Intent, Current State, Decisions, Next Actions, and Persistent Memory. Your intelligence travels with you across sessions, devices, and employers.

**2. FirmOS** — the trust layer that makes your agent enterprise-ready. When you walk into work, FirmOS is your agent's work visa. It governs what the agent can access inside a company's systems, keeps the boundaries clean, and satisfies the CISO before they ask.

### FirmOS Security Architecture

| Layer | Mechanism | Purpose |
|---|---|---|
| **In-band** | Evals, test harnesses, internal firewall | Governs agent behavior before it runs |
| **Out-of-band** | Gateway, proxy, external firewall | Monitors every action at runtime |
| **Result** | CISO-compliant personal agent | Enterprise says yes |

---

## Architecture

```
You (anywhere — phone, park, office, Slack)
        ↕
Intent Inbox        ← capture intent, queue offline, route online
        ↕
Chief of Staff      ← Nemotron ULTRA: portfolio view, deep reasoning
        ↕
Intent Router       ← Nemotron NANO: fast classification, project matching
        ↕
Project Brains      ← structured memory: goal / state / decisions / actions / memory
        ↕
FirmOS              ← trust boundary: in-band + out-of-band security
        ↕
Corporate Systems   ← Salesforce, Slack, GitHub, any connected tool
```

**Offline-first:** When there is no connectivity, intents are captured locally and queued. When back online, the full Nemotron pipeline processes the queue. Your agent works while you're present with your family — findings are ready when you reconnect.

---

## NVIDIA Nemotron on Nebius Token Factory

All inference runs on **Nebius Token Factory** using NVIDIA open source models:

| Model | Used For |
|---|---|
| `nvidia/Nemotron-3-Ultra-550b-a55b` | Chief of Staff — deep reasoning, Project Brain updates |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | Intent routing — fast classification (~100ms) |
| `nvidia/nemotron-3-super-120b-a12b` | Project Manager triage, task planning |
| `nvidia/Nemotron-3_5-Lightning` | High-frequency calls, projection generation |
| `NousResearch/Hermes-4-405B` | Tool calling, agentic loops |

**Two-stage pipeline per intent:**
1. Nemotron NANO classifies the intent and routes to the right project (fast, ~100ms)
2. Nemotron ULTRA generates the full Project Brain update (deep, ~2s)

**Offline fallback:** `ollama/nemotron-mini` runs on-device via Ollama for basic intent capture without connectivity. See `anywhere/offline.py`.

---

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Nebius Token Factory API key ([tokenfactory.nebius.com](https://tokenfactory.nebius.com))

### Install

```bash
git clone https://github.com/VGBRO/anywhere-stack.git
cd anywhere-stack
uv sync
```

### Replit workspace

The web app is at `artifacts/anywhere-web/index.html`; it preserves the original
Apple-style UI and Canvas landscape with the scoped Firm OS/filter update.
The Python package and FastAPI service live in `artifacts/api-server/anywhere/`.
This is a pnpm multi-app workspace. The Expo mobile companion lives in
`artifacts/anywhere-mobile/` and embeds the Liquid Glass interface from upstream
commit `00ef0ce`, stored unchanged at
`artifacts/anywhere-web/public/mobile-source.html`. The mobile snapshot is
independent of the web home; `public/index.html` remains the upstream interface.
Mobile Face/Voice sign-in and responses are demonstrations, not identity
verification or live AI. The mobile wrapper needs the web service running.

Click Run using these managed workflows:

- `artifacts/anywhere-web: web` — Vite serves the existing vanilla HTML at `/`.
- `artifacts/api-server: API Server` — Python 3.11 / FastAPI via
  `uv run --frozen python main.py`, bound to `PORT`.
- `artifacts/anywhere-mobile: expo` — Expo Go and browser mobile previews.
  On Replit, the workflow supplies `EXPO_PUBLIC_DOMAIN` automatically.
  Outside Replit, set it to the web service host (without `https://`) when
  starting Expo; device previews require a host reachable from the phone.

The shared proxy keeps `/api/*`, `/health`, `/static/*`, `/docs`, `/redoc`,
and `/openapi.json` on the same origin as the web UI. No custom API host or
Vite proxy is needed. For shell checks in Replit use `http://localhost:80/health`.

Install workspace dependencies with `pnpm install --frozen-lockfile` and
Python dependencies with `uv sync --frozen`. The post-merge script does both.
No database is required; the scaffold's database packages are unused.
FastAPI remains the source of the existing API schema at `/openapi.json`;
the scaffold's generated TypeScript client is not used by the vanilla UI.

### Configure

On Replit, keep `NEBIUS_API_KEY` in **Secrets** and restart the API workflow
after changes. No `.env` file is required. Never put keys in browser code or Git.
`/health` reports configuration presence only, not provider validity.
Missing credentials return 503; provider or malformed AI responses return 502.
Failed sync items retain their existing per-item error envelope, not fake success.

**Existing security boundary:** The imported intent/sync API has no authentication,
rate limits, or spending limits. The prototype's biometric screens are demonstrations,
not API access control. Keep the workspace private and add real access control and
abuse limits before making credential-backed inference available to untrusted users.
This port does not add a login flow or change the original API access contract.

For local development only:

```bash
cp .env.example .env
# Add your NEBIUS_API_KEY to .env
```

### Start the API server

```bash
bash scripts/serve.sh
# → http://localhost:8080 (or PORT)
```

### Open the prototype UI

```bash
# Replit: open the Anywhere Stack web preview.
# Local: the standalone FastAPI service also serves the same HTML at /
open http://localhost:8080
```

### Verify Nemotron connection

```bash
curl http://localhost:80/health
```

Expected:
```json
{
  "status": "ok",
  "nebius_configured": true,
  "models": {
    "router": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    "cos": "nvidia/Nemotron-3-Ultra-550b-a55b"
  },
  "provider": "Nebius Token Factory"
}
```

### Test a live Nemotron intent

```bash
curl -X POST http://localhost:80/api/intent \
  -H "Content-Type: application/json" \
  -d '{"text": "Plan an ADU in my backyard, go ahead", "projects": []}'
```

---

The prototype still starts with the upstream sample projects. State and queued
intents are held in browser memory, not durable storage; reloading loses them.
Some voice interactions remain upstream local demonstrations, not live AI.
Web home intent and sync requests use FastAPI. The preserved upstream web
prototype falls back to local demo updates on provider failures and can clear
unprocessed queued intents after a sync attempt. Neither UI should be treated
as durable storage or production authentication.

## API Reference

### `POST /api/intent`

Process a natural language intent through the two-stage Nemotron pipeline.

**Request:**
```json
{
  "text": "I want to build an ADU in my backyard by next summer",
  "projects": [
    { "id": "infrastructure", "name": "India AI Infrastructure", "tags": ["india", "ai"], "state": "...", "goal": "..." }
  ]
}
```

**Response:**
```json
{
  "project_id": "new",
  "project_name": "Backyard ADU",
  "is_new": true,
  "action_type": "plan",
  "routing_confidence": 0.92,
  "response": "Absolutely — I'll handle the ADU planning from permits to punch lists while you and Bira soak up the backyard sunshine.",
  "brain": {
    "goal": "Build a permitted, move-in-ready ADU in the backyard",
    "state": "Planning phase initiated",
    "decision": "Execute comprehensive ADU planning autonomously",
    "actions": ["Research local ADU zoning requirements", "..."],
    "memory": "Dog: Bira; user prefers hands-off planning with approval gates"
  },
  "models_used": {
    "router": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    "cos": "nvidia/Nemotron-3-Ultra-550b-a55b",
    "provider": "Nebius Token Factory"
  }
}
```

### `POST /api/sync`

Flush the offline intent queue through Nemotron when back online.

### `GET /health`

Returns API status and configured model IDs.

---

## Offline Mode

When offline, the UI captures intents locally using keyword matching and queues them. When connectivity is restored, the full Nemotron pipeline processes each queued intent and updates the Project Brain.

For on-device local inference (Option A — long-term architecture):

```bash
brew install ollama
ollama serve &
ollama pull nemotron-mini   # ~4GB, runs on Apple Silicon
```

The `anywhere/offline.py` module auto-detects Ollama and uses `nemotron-mini` if available, falling back to `llama3.2:1b`, falling back to keyword matching.

---

## Project Structure

```
anywhere-stack/
├── anywhere/
│   ├── api.py          ← FastAPI server — Nemotron intent pipeline
│   ├── client.py       ← Nebius Token Factory client (5 Nemotron models)
│   ├── offline.py      ← Ollama local model integration
│   ├── roles/
│   │   ├── cos.py      ← Chief of Staff role (Nemotron ULTRA)
│   │   ├── pm.py       ← Project Manager role (Nemotron SUPER)
│   │   └── builder.py  ← Builder role (Hermes tool calling)
│   ├── connectors/     ← Slack, GitHub, Google Meet
│   └── interfaces/     ← Slack event handling
├── projects/           ← Project Brain repositories
├── scripts/
│   └── serve.sh        ← Start the API server
├── public/             ← Web UI prototype
├── .env.example
└── pyproject.toml
```

---

## Hackathon Notes

Built for the **NVIDIA × Nebius Global AI Hackathon 2026** (Personal AI track).
Submission deadline: October 30, 2026.

**Nebius Token Factory usage:**
- All Nemotron model inference runs on Nebius Token Factory
- Two-stage pipeline: NANO for routing (cost-efficient), ULTRA for reasoning (quality)
- OpenAI-compatible API via `anywhere/client.py`

**NVIDIA models used:** Nemotron-3-Ultra-550b, Nemotron-3-Nano-30B, Nemotron-3-Super-120b, Nemotron-3.5-Lightning, Hermes-4-405B

**Significant updates during submission period:**
- FirmOS trust layer design and in-band/out-of-band security architecture
- FastAPI server (`anywhere/api.py`) wiring the web UI to live Nemotron inference
- Offline intent queue with Nemotron sync on reconnect
- Ollama local model integration for on-device fallback (`anywhere/offline.py`)
- Web prototype UI with Project Brain, offline mode, and FirmOS badges

---

## License

MIT — see [LICENSE](LICENSE)
