# Model Routing Strategy

## Why Claude

Anywhere Stack uses Claude because the goal is persistent personal intelligence — not just fast inference. Claude Opus's context window, reasoning quality, and instruction-following make it the right model for a Chief of Staff that needs to hold a full portfolio in mind and make nuanced routing decisions.

The three-tier model strategy maps to distinct capability requirements:

| Model | Role | Characteristic |
|---|---|---|
| Claude Haiku | On-device / intent routing | Fast (~100ms), lightweight, cheap |
| Claude Sonnet | Project Manager | Balanced reasoning + planning |
| Claude Opus | Chief of Staff | Deep reasoning, full context |

## Model IDs

```python
OPUS   = "claude-opus-4-5"    # CoS heartbeat, complex reasoning
SONNET = "claude-sonnet-4-5"  # PM triage, task planning
HAIKU  = "claude-haiku-4-5"   # Fast routing, classification
```

## Anthropic API Setup

```bash
# Get a key at console.anthropic.com
export ANTHROPIC_API_KEY=sk-ant-...
```

The client is a thin wrapper over the Anthropic Python SDK (`anthropic` package). See `anywhere/client.py`.

## Offline Fallback

When `ANTHROPIC_API_KEY` is unavailable or the network is down, intents are queued locally. Optionally, a local Ollama model handles basic classification:

```bash
brew install ollama
ollama pull llama3.2:1b   # ~1.3GB
```

See `anywhere/offline.py`.
