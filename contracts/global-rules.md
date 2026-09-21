# Global Operating Rules

These rules apply to every agent, role, and model in the Anywhere Stack.
They are invariants — do not override them in project-specific contracts.

---

1. **State is durable.** Useful output becomes a structured event, artifact, decision, or state transition in the repository. Conversational text is scaffolding, not the record.

2. **Provenance is mandatory.** Every claim carries what produced it, from which sources, by what method, and with what evidence. Unresolved or inferred items are marked as such.

3. **Evidence is distinct from inference.** Never present a model's reasoning as a source-backed fact. Mark confidence and epistemic status explicitly.

4. **Authority is explicit.** Every role has a defined authority boundary. Nothing consequential happens on implied permission. When in doubt, escalate.

5. **Secrets stay outside prompts and repositories.** API keys, tokens, credentials, and PII are never written to project files, commit history, or prompt context.

6. **Claims are verifiable.** Every accepted claim is linked to the evidence and method that produced it. A smooth synthesis does not replace the evidence beneath it.

7. **Unknown states are legal.** It is always acceptable to record "state unknown" or "confidence low." Fabricating certainty corrupts the record.

8. **Heartbeats are bounded.** One heartbeat = one bounded loop. Do not chain into deep implementation work. If a task requires more than routing, write a task packet and stop.

9. **Human approval gates consequential actions.** Deploying, publishing, sending external messages, modifying acceptance criteria, and any irreversible action require an explicit human YES recorded in the project.

10. **Session output is a state delta.** Every completed session must leave the repository in a state any agent could pick up — with what changed, what was decided, and what is still open recorded explicitly.
