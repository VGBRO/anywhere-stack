# Anywhere Stack Architecture

## Repo-Centric Design
The Anywhere Stack follows a repo-centric design where the Git repository serves as the single source of truth for all project state, configuration, and artifacts. All changes flow through the repository via pull requests, ensuring auditability, reproducibility, and collaboration. The system treats the repo as the central coordination mechanism, with agents (PM, Builder) interacting exclusively through repo operations (commits, PRs, issues). This design enables:
- Immutable history of all decisions and changes
- Automatic triggering of workflows via repo events
- Easy rollback and forensic analysis
- Distributed operation without central bottlenecks

## Roles: CoS, PM, Builder

### Chief of Staff (CoS)
The CoS oversees the entire operational framework, ensuring alignment with strategic objectives. Responsibilities include:
- Defining and evolving the Anywhere Stack methodology
- Resolving cross-functional impediments
- Maintaining organizational health and adoption
- Acting as escalation point for systemic issues

### Project Manager (PM)
The PM manages the tactical execution flow within the repo-centric system:
- Reconciling state from issues, PRs, and agent outputs
- Sequencing work based on priorities and dependencies
- Delegating bounded tasks to Builders via issue creation
- Monitoring health metrics and blockers
- Ensuring adherence to invariants and acceptance criteria

### Builder
Builders execute discrete, bounded tasks with strict authority boundaries:
- Implementing only what is specified in task packets
- Recording all decisions with evidence (typically in generated documents)
- Never altering acceptance criteria or project invariants
- Exiting immediately after task completion, leaving the repo in a legible state
- Escalating to PM when encountering out-of-scope requirements or discovered constraints

## Nemotron Model Tiers
The architecture leverages NVIDIA's Nemotron model family across three tiers to optimize for different workload characteristics:

### Nemotron-3 Nano
- Optimized for lightweight, high-frequency tasks
- Used for simple classification, routing, and initial triage
- Deployed in agent feedback loops where latency is critical
- Typical use: Issue parsing, basic validation, metadata extraction

### Nemotron-3 Super
- Balanced tier for general-purpose reasoning and generation
- Handles most agent decision-making and content creation
- Employed for task decomposition, planning, and standard documentation
- Typical use: Architecture drafting, plan generation, code commenting

### Nemotron-3 Ultra
- Highest capability tier for complex reasoning and synthesis
- Reserved for strategic analysis, architectural decisions, and nuanced interpretation
- Used when multiple contexts must be synthesized or ambiguity is high
- Typical use: Acceptance criteria refinement, invariant validation, retrospective analysis

Models are selected dynamically based on task complexity scores calculated by the PM during delegation.

## Slack Interface
Slack serves as the primary human-interaction layer for the Anywhere Stack, providing:

### Notification Channels
- `#anywhere-alerts`: Critical system health and blocker notifications
- `#anywhere-completions`: Automated announcements of finished tasks and milestones
- `#anywhere-debug`: Detailed agent logs for troubleshooting (opt-in)

### Interactive Commands
- `/anywhere status`: Returns current phase, health, and next action from `state.md`
- `/anywhere help`: Lists available commands and usage guidelines
- `/anywhere trigger <task-name>`: Manually initiates a predefined task workflow (CoS/PM only)

### Workflow Integration
- Slack messages can generate issues via slash commands (e.g., `/anywhere issue "New feature request"`) 
- PR reviews and comments can be mirrored to relevant Slack channels for visibility
- Agents post progress updates to threads associated with specific issue IDs

The Slack interface maintains loose coupling—agents never depend directly on Slack for core logic, ensuring the system remains functional even if Slack connectivity is temporarily lost.