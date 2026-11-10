# Anywhere Stack

**A repo-centric modular agent stack powered by Claude (Anthropic).**

> The hardware gets you online. The control plane makes work portable.

---

## Mission

Make AI work portable, private, and persistent — from anywhere, on open infrastructure.
Any agent can enter, understand the current state, do bounded work, and leave a legible state transition.

## Architecture

```
human (Slack mobile)
    ↕
Chief of Staff  ←→  portfolio projections
    ↕
Project Managers  ←→  project state (repos)
    ↕
Builders / Reviewers  ←→  tasks, evidence, artifacts
    ↕
Repository (canonical history + derived projections)
```

## Models

| Model | Use |
|-------|-----|
| `claude-opus-4-5` | CoS heartbeat, complex reasoning |
| `claude-sonnet-4-5` | PM triage, task planning |
| `claude-haiku-4-5` | Fast routing, classification |
| `claude-haiku-4-5` | High-frequency, cheap calls |

## Entry Points

- `anywhere heartbeat` — run CoS heartbeat across portfolio
- `anywhere heartbeat <project>` — run PM heartbeat for a project
- `anywhere status` — show portfolio health
- `anywhere init <name>` — initialize a new project repo
- `anywhere slack` — start the Slack listener (mobile interface)
- `anywhere test-claude — verify Anthropic connection

## Key Files

| File | Role |
|------|------|
| `contracts/global-rules.md` | Invariants for all agents |
| `contracts/cos.md` | Chief of Staff role contract |
| `contracts/pm.md` | Project Manager role contract |
| `contracts/builder.md` | Builder role contract |
| `skills/cos-skill.md` | CoS heartbeat procedure |
| `skills/pm-skill.md` | PM heartbeat procedure |
| `skills/builder-skill.md` | Builder task execution procedure |
| `projects/` | Your project repos live here |

## Instruction Stack (layered)

```
4. Task context       — current objective, files, constraints
3. Project contract   — mission, invariants, acceptance criteria
2. Role skill         — procedure for this role
1. Global rules       — invariants across all roles and projects
```

## Durable State Pattern

```
event history → projection logic → current state
```

- Canonical: `runs/*.json` (append-only events), `decisions.md`, `evidence/`
- Projections: `state.md` (machine), `brief.md` (human) — regenerated from canonical, always stale-ok

## Human Interface

- Slack: mention the bot or send `heartbeat` in any channel
- CLI: `anywhere <command>` from any terminal
- Any AI can resume by reading `agent-os.md` + `state.md` + `brief.md`
