# Nemotron Integration — Model Routing Strategy

## Why Nemotron

NVIDIA's Nemotron model family is the technical foundation for Anywhere Stack's reasoning capabilities. The choice is strategic, not incidental.

**The real reason: Salesforce KOA.**

Salesforce is building **KOA** — a family of enterprise AI models built on the Nemotron architecture. KOA is Salesforce's bet on what enterprise-grade reasoning models look like at different capability tiers.

Anywhere Stack was built on Nemotron because it is the same architectural foundation as KOA. The five-tier routing strategy in this codebase — NANO for classification, ULTRA for deep reasoning, SUPER for planning, HERMES for tool use, LIGHTNING for high-frequency ops — is a direct preview of how KOA-tiered inference would work in a production personal AI stack.

This is not a hackathon convenience. It is deliberate alignment: **this prototype shows what a KOA-native personal agent looks like before KOA ships.**

**Additional reasons Nemotron is the right choice:**
1. **Scale range.** One family covers 30B to 550B parameters — same API, same provider, radically different cost/quality tradeoffs. Most providers give you small models or large ones, not a coherent family spanning both.

2. **Reasoning quality at the top.** The 550B Ultra model is among the strongest available for complex multi-step reasoning. The Chief of Staff role requires this level — synthesizing a portfolio of projects, understanding relationships between intents, making non-obvious connections.

3. **Speed at the bottom.** The 30B Nano model handles intent routing in ~100ms. The user perceives no latency between typing and the first stage completing.

4. **Hackathon infrastructure.** The NVIDIA × Nebius hackathon provides native access through the Nebius Token Factory — same models, no additional setup.

---

## The Nebius Token Factory

All Nemotron inference runs through the **Nebius Token Factory** — an OpenAI-compatible inference API.

```
Base URL: https://api.tokenfactory.nebius.com/v1/
Auth:     Authorization: Bearer $NEBIUS_API_KEY
Protocol: OpenAI Chat Completions format
```

Because it uses the OpenAI protocol, the existing Python `openai` library works without modification. The only change is `base_url` and the API key.

```python
# client.py
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("NEBIUS_API_KEY"),
    base_url="https://api.tokenfactory.nebius.com/v1/"
)
```

This means the entire Nemotron integration required zero changes to inference code — only routing logic needed to be added on top.

---

## The Five Model Tiers

The Nemotron family provides five distinct tiers for different tasks:

### NANO — Intent Router
```
Model ID: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
Size:     30B parameters
Latency:  ~100ms
Cost:     ~1/18th of ULTRA
Use case: Intent routing — which project does this belong to?
```

Routing is a pattern matching problem. Given "plan my backyard project," the model needs to:
1. Look at a list of 3–10 projects
2. Decide which project this belongs to (or that it's new)
3. Classify the action type (update/research/plan/task/decision)
4. Return a confidence score

A 30B model handles this reliably. There is no deep reasoning required — the match is usually obvious. Using the 550B model for this would be a 18x cost multiplier for no quality gain.

---

### ULTRA — Chief of Staff
```
Model ID: nvidia/Nemotron-3-Ultra-550b-a55b
Size:     550B parameters
Latency:  ~2s
Cost:     Highest
Use case: Project Brain updates — synthesize intent + context → structured output
```

This is the heavyweight. The ULTRA model handles the Chief of Staff role: given an intent and the full project context, reason through what changed, what it means, and generate a rich structured update across all five Project Brain sections.

This task requires genuine understanding:
- "What does this new development mean for the project's current state?"
- "Does this change the decision we made last week?"
- "What should the next actions be given this new information?"
- "What should never be forgotten about this?"

A small model produces generic outputs here. The ULTRA model produces responses that feel like a thoughtful executive assistant who knows the project deeply.

---

### SUPER — Project Manager
```
Model ID: nvidia/nemotron-3-super-120b-a12b
Size:     120B parameters
Latency:  ~500ms
Cost:     Mid
Use case: Task planning, sequencing, PM-level triage
```

The Project Manager role sits between routing (simple) and CoS reasoning (complex). It handles:
- Breaking down a high-level goal into a sequence of tasks
- Estimating effort and ordering by dependency
- Identifying blockers

The 120B size provides enough reasoning depth for multi-step planning without the latency and cost of the 550B model.

---

### LIGHTNING — High-Frequency Operations
```
Model ID: nvidia/Nemotron-3_5-Lightning
Size:     Fast variant
Latency:  <50ms
Cost:     Lowest
Use case: Projection generation, formatting, high-frequency calls
```

For tasks that run many times per session — generating a brief summary, formatting an action list, converting between representations — Lightning provides extremely low latency at minimal cost. Not used for reasoning, only for transformation.

---

### HERMES — Tool Calling
```
Model ID: NousResearch/Hermes-4-405B
Size:     405B parameters
Latency:  ~1.5s
Cost:     High
Use case: Agentic loops with structured tool use
```

Hermes-4 is specifically strong at structured tool calling — the pattern where an agent generates a tool invocation, receives the result, and uses it in the next step. This is the workhorse for future agentic workflows (research loops, document generation, multi-step data assembly).

Note: Hermes-4 is a NousResearch model, not an NVIDIA model. It is available on the same Nebius Token Factory endpoint, making it accessible without additional infrastructure.

---

## The Two-Stage Pipeline (Live Today)

The current implementation uses two of the five tiers:

```
User types intent
       │
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │  STAGE 1: NANO Router                                    │
  │                                                          │
  │  Input:  intent text + project list (name, id, tags)     │
  │  Output: { project_id, project_name, is_new,             │
  │             action_type, confidence }                    │
  │                                                          │
  │  Time:   ~100ms                                         │
  └──────────────────────────────────────────────────────────┘
       │
       │ pass matched project context forward
       ▼
  ┌──────────────────────────────────────────────────────────┐
  │  STAGE 2: ULTRA Chief of Staff                          │
  │                                                          │
  │  Input:  intent text + project name + current Brain     │
  │  Output: { response (warm ack), brain (all 5 sections) }│
  │                                                          │
  │  Time:   ~2s                                            │
  └──────────────────────────────────────────────────────────┘
       │
       ▼
  UI updates project card with new Brain content
```

---

## Graceful Degradation

The pipeline has explicit fallback logic at both stages:

```python
# Stage 1 fallback — if NANO fails
routing = {
    "project_id": "new",
    "project_name": "New Project",
    "is_new": True,
    "action_type": "plan",
    "confidence": 0.5,
}

# Stage 2 fallback — if ULTRA fails
cos_result = {
    "response": f"Got it. I'll work on {project_name} for you.",
    "brain": {
        "goal": matched_project_goal,
        "state": f"Intent captured: {intent_text}",
        "decision": "",
        "actions": ["Review intent and define next steps."],
        "memory": "",
    }
}
```

The fallback is designed to be useful, not just safe. It captures the intent and routes it to a new project — the user can manually assign later. No data is lost.

---

## Offline Mode

When the device has no network access, the Nemotron pipeline is bypassed entirely. The intent is:
1. Classified via keyword matching (if Ollama is unavailable)
2. Or classified via Ollama + nemotron-mini (on-device inference, Option A)
3. Stored in `LocalQueue[]` in browser memory
4. Flushed through the full two-stage pipeline when connectivity returns

The offline classification is intentionally degraded — keyword matching cannot do the deep Project Brain synthesis. But it captures the intent, routes it to the most likely project, and preserves it for full processing when back online.

This means a user at the park, on a plane, or in a dead zone never loses an intent. Every capture feeds into the same intelligent pipeline, just with a time delay.

---

## Cost Model (Approximate)

One complete intent → Project Brain update cycle:

| Stage | Model | Tokens (estimate) | Relative cost |
|---|---|---|---|
| NANO routing | Nemotron 30B | ~200 in, ~100 out | 1× |
| ULTRA CoS | Nemotron 550B | ~800 in, ~400 out | ~18× |
| **Total per intent** | | **~1,500 tokens** | **~19× base** |

For a typical day with 10–20 work intents, the total cost is well within hackathon demo budgets. At production scale, caching Project Brain state and batching low-priority intents reduces cost further.

---

## The Rationale for Two-Stage Over One-Stage

An alternative design would use a single ULTRA call to do both routing and Brain synthesis. This is simpler to implement but strictly worse:

| Dimension | One-stage (ULTRA only) | Two-stage (NANO + ULTRA) |
|---|---|---|
| Cost per intent | 18× base | ~19× base (marginal difference) |
| Latency | ~2s (ULTRA full input) | ~2.1s (100ms NANO + 2s ULTRA) |
| Routing accuracy | High | High |
| Brain quality | High | High |
| **Correctability** | Low | **High** |

The two-stage design allows the routing decision to be audited, overridden, and cached independently of the Brain synthesis. If routing is wrong (wrong project), the ULTRA call was wasted — but with two stages, you see the routing decision before it's used. The architecture is observable.

More importantly: as the system grows, different routing models can be swapped in without touching the CoS layer. The two-stage boundary is a seam — it allows independent evolution.

---

## Model Configuration (Codebase)

All model IDs are defined in `anywhere/client.py` as an enum:

```python
class Model(str, Enum):
    ULTRA    = "nvidia/Nemotron-3-Ultra-550b-a55b"
    SUPER    = "nvidia/nemotron-3-super-120b-a12b"
    HERMES   = "NousResearch/Hermes-4-405B"
    NANO     = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
    LIGHTNING = "nvidia/Nemotron-3_5-Lightning"
```

The API layer (`anywhere/api.py`) imports `Model.NANO` and `Model.ULTRA` directly — no magic strings scattered through the codebase. Swapping a model requires a one-line change in `client.py`.
