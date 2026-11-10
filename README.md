# Anywhere Stack

A personal AI that knows you — and can follow you to work.

**[Live demo → anywhere-stack.replit.app](https://anywhere-stack.replit.app)**

---

"For the first time in history, we're entering a world where billions of people could have their own personal AI agents. Agents that know us. Remember our goals. Understand how we work."

And yet, there's still a wall.

The moment you walk into work, you leave your personal agent at the front door. You're back to tools that don't know you. You rebuild context, explain your priorities, start from zero.

But there's a reason that wall exists. Companies cannot allow untrusted agents to access their systems, their customers, or their data.

So how do we make personal intelligence portable without compromising enterprise security? That's why I built Anywhere Stack and FirmOS.

---

Anywhere Stack is your persistent personal AI operating system. My Chief of Staff remembers all of my projects. Every project has a persistent brain: goals, decisions, state, actions, and memory. The context doesn't disappear when the conversation ends.

In my professional environment, the agent experience stays the same. But company context, permissions, and actions remain inside the enterprise's trust boundary.

These agents will touch multiple applications, systems, and surfaces. Securing the model alone isn't enough. We need two independent layers of protection.

**In-band security** — built into the agent's execution path. Evals, test harnesses, guardrails, and an internal policy firewall determine what the agent can do before it acts.

**Out-of-band security** — an independent runtime enforcement layer. Gateways, proxies, and policy controls observe and govern every agent interaction with enterprise systems.

It's a personal agent that your company's CISO doesn't have to trust blindly. The enterprise controls the boundary, the permissions, and the actions. That's the purpose of FirmOS.

---

Anywhere Stack runs on Claude. On device, Claude Haiku handles fast intent capture and local context — lightweight enough to work in constrained environments. In the cloud, Claude Opus gives the Chief of Staff deep understanding of your projects, priorities, and how you think. Claude Sonnet handles planning and task triage in between.

The context doesn't live in the model. It lives in your Project Brain — a structured file you own, under version control you control. Any model can pick it up and continue.

We're building for a future where personal agents are as common as smartphones. When you change devices, jobs, or environments, your personal intelligence should move with you. The enterprise remains protected. The individual keeps their intelligence.

That is Anywhere Stack.

---

## How the AI works

| Model | Role | What it does |
|---|---|---|
| Claude Haiku | On-device | Fast intent capture, local context routing (~100ms) |
| Claude Sonnet | Project Manager | Task planning, triage, project heartbeats (~1s) |
| Claude Opus | Chief of Staff | Deep reasoning, cross-project strategy, portfolio oversight (~2s) |
| Web Speech API | Speech-to-text | Browser-native transcription; works offline |
| Tavily Search | Research tool | Real-time web search for current facts |

All cloud inference uses the **Anthropic API**. Get a key at [console.anthropic.com](https://console.anthropic.com).

---

## Try it

Open `public/index.html` in any browser. No install required.

Tap the voice orb. Say anything. Watch your Project Brain populate in real time.

---

## Run it locally

```bash
git clone https://github.com/VGBRO/anywhere-stack.git
cd anywhere-stack
open public/index.html
```

The web UI runs without any API keys. For live Claude inference:

```bash
uv sync
cp .env.example .env
# Add ANTHROPIC_API_KEY — get one at console.anthropic.com
bash scripts/serve.sh
# → http://localhost:8080
```

Voice recognition needs HTTPS or localhost. To test on mobile:

```bash
python3 -m http.server 8080 --directory public
# open http://localhost:8080 on your phone
```

---

## Replit

Click **Run**. Three workflows start:

- `anywhere-web` — the Liquid Glass web UI
- `api-server` — FastAPI + Nemotron intent pipeline
- `anywhere-mobile` — Expo mobile companion

Add `ANTHROPIC_API_KEY` to Replit Secrets before you run.

---

## Security

- Never commit API keys. Use `.env` locally and Replit Secrets on Replit.
- The API has no authentication. Keep the workspace private until you add access control.
- Biometric screens in the mobile app are demonstrations, not identity verification.
- Rotate any exposed key at [console.anthropic.com](https://console.anthropic.com).

---

## Project structure

```
anywhere-stack/
├── public/                 ← Web UI — open this for the demo
│   └── index.html
├── anywhere/               ← Python package
│   ├── api.py              ← FastAPI server
│   ├── client.py           ← Anthropic API client
│   ├── offline.py          ← On-device fallback (Web Speech API / Whisper)
│   └── roles/              ← Chief of Staff, PM, Builder roles
├── artifacts/
│   ├── anywhere-mobile/    ← Expo mobile app (React Native)
│   ├── anywhere-web/       ← Replit web wrapper
│   └── api-server/         ← Replit API package
├── projects/               ← Project Brain YAML files
├── .env.example
└── pyproject.toml
```

---

## Built with

**Anthropic Claude** — Haiku (on-device), Sonnet (planning), Opus (Chief of Staff). API at [console.anthropic.com](https://console.anthropic.com).

**Tavily** — Real-time web search wired into the agent's tool-calling loop. When Claude knows your context but needs current facts — permit requirements, contractor rates, live regulations — it calls Tavily.

**Claude Code** — The entire stack was built and iterated using Claude Code as the development environment.

---

## License

MIT — see [LICENSE](LICENSE)

Built by [Varun Guruvugari](https://github.com/VGBRO)
