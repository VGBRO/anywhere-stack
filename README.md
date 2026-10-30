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

Anywhere Stack runs on NVIDIA Nemotron. On device, NVIDIA Parakeet — a sub-1B model that handles speech-to-text offline, so the agent works even without a connection. In the cloud, Nemotron Ultra 550B on Nebius gives the agent deep understanding of my projects, my priorities, and how I think.

I'm not an ML engineer. Nebius Token Factory let me write evals and fine-tune Nemotron on my own context. That's the part that surprised me most. You don't need a team to make a model that knows you.

We're building for a future where personal agents are as common as smartphones. When you change devices, jobs, or environments, your personal intelligence should move with you. The enterprise remains protected. The individual keeps their intelligence.

That is Anywhere Stack.

---

## How the AI works

| Model | What it does |
|---|---|
| Nemotron Nano 30B | Classifies your intent and routes to the right project (~100ms) |
| Nemotron Ultra 550B | Reads your Project Brain and writes the full response (~2s) |
| Nemotron Super 120B | Plans tasks and manages project triage |
| NVIDIA Parakeet (NeMo) | Streams speech to text; works offline on-device |

All cloud inference runs on **Nebius Token Factory**.

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

The web UI runs without any API keys. For live Nemotron inference:

```bash
uv sync
cp .env.example .env
# Add NEBIUS_API_KEY — get one at tokenfactory.nebius.com
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

Add `NEBIUS_API_KEY` to Replit Secrets before you run.

---

## Security

- Never commit API keys. Use `.env` locally and Replit Secrets on Replit.
- The API has no authentication. Keep the workspace private until you add access control.
- Biometric screens in the mobile app are demonstrations, not identity verification.
- Rotate any exposed key at [tokenfactory.nebius.com](https://tokenfactory.nebius.com).

---

## Project structure

```
anywhere-stack/
├── public/                 ← Web UI — open this for the demo
│   └── index.html
├── anywhere/               ← Python package
│   ├── api.py              ← FastAPI server
│   ├── client.py           ← Nebius Token Factory client
│   ├── offline.py          ← On-device fallback (Parakeet / Ollama)
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

## Hackathon

NVIDIA × Nebius Global AI Hackathon 2026 — Personal AI track.

**NVIDIA models:** Parakeet (NeMo), Nemotron Nano 30B, Nemotron Super 120B, Nemotron Ultra 550B.

**Nebius:** All cloud inference and personal fine-tuning runs on Nebius Token Factory.

---

## License

MIT — see [LICENSE](LICENSE)

Built by [Varun Guruvugari](https://github.com/VGBRO)
