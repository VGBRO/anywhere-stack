"""Slack connector for the Teamwork Graph.

Two responsibilities:

  1.  SlackConnector
      Fetches threads and canvases from watched Slack channels.
      Qualifies threads by signal markers or ✅ reaction.
      Adds raw objects to the ActiveGraph graph — not files, not logs.
      Those raw objects trigger the extraction behaviors below.

  2.  Extraction behaviors
      slack_thread_extractor  — fires on slack_thread_raw objects
      slack_canvas_extractor  — fires on slack_canvas_raw objects
      Both call Nemotron-Super to extract Decision / Task / Blocker /
      Person entities and write them with epistemic_state=proposed.

Public API:
  SlackConnector(project_root, graph, watched_channels)
    .sweep(since_ts)        poll all watched channels since a timestamp
    .ingest_thread(ch, ts)  fetch + add one thread; returns True if new
    .ingest_canvas(file_id) fetch + add one Canvas; returns True if new

  make_teamwork_runtime(graph, project_root) -> Runtime
    create a Runtime with both extraction behaviors registered

Note on LLM provider:
  Extraction uses anywhere.client.reason() (Nebius/Nemotron) directly
  rather than activegraph's @llm_behavior, which requires an ActiveGraph
  LLM provider configured for the Nebius endpoint. Migrate to
  @llm_behavior once that provider is wired up.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from activegraph import Graph, Runtime
from activegraph.behaviors.decorators import behavior

from anywhere.client import reason, Model
from anywhere.state.canonical import append_event, parse_json


# ── Signal markers ───────────────────────────────────────────────────────────

_DECISION_MARKERS = [
    "we decided", "going with", "final call", "we're going with",
    "we will use", "approved", "agreed on", "chose", "selected",
    "the decision is", "decided to",
]
_TASK_MARKERS = [
    "i'll take", "i will", "assigned to", "action item",
    "by eod", "by end of", "this week", "will do", "taking this",
]
_BLOCKER_MARKERS = [
    "blocked", "waiting on", "waiting for", "can't proceed",
    "stuck on", "depends on", "need to unblock", "haven't been able",
]
_RESOLVED_REACTION = "white_check_mark"   # ✅

_DEDUPE_FILE = ".slack_ingested.json"


# ── Deduplication ────────────────────────────────────────────────────────────

def _load_dedupe(project_root: str) -> dict:
    path = Path(project_root) / _DEDUPE_FILE
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def _save_dedupe(project_root: str, store: dict) -> None:
    (Path(project_root) / _DEDUPE_FILE).write_text(json.dumps(store, indent=2))


def _already_ingested(project_root: str, key: str, item_id: str) -> bool:
    return item_id in _load_dedupe(project_root).get(key, [])


def _mark_ingested(project_root: str, key: str, item_id: str) -> None:
    store = _load_dedupe(project_root)
    store.setdefault(key, [])
    if item_id not in store[key]:
        store[key].append(item_id)
    _save_dedupe(project_root, store)


# ── Thread qualification ─────────────────────────────────────────────────────

def _has_resolved_reaction(root_message: dict) -> bool:
    return any(
        r.get("name") == _RESOLVED_REACTION
        for r in root_message.get("reactions", [])
    )


def _qualify_thread(messages: list[dict]) -> tuple[bool, str]:
    """Return (qualifies, reason). Qualifies if ✅ reaction OR signal markers present."""
    if not messages:
        return False, "empty"
    if _has_resolved_reaction(messages[0]):
        return True, "resolved_reaction"
    full_text = " ".join((m.get("text") or "").lower() for m in messages)
    for marker in _DECISION_MARKERS + _TASK_MARKERS + _BLOCKER_MARKERS:
        if marker in full_text:
            return True, f"marker:{marker}"
    return False, "no_signal"


# ── Slack API helpers ────────────────────────────────────────────────────────

def _make_client() -> WebClient:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN not set.")
    return WebClient(token=token)


def _resolve_channel_id(client: WebClient, channel: str) -> str:
    """Resolve #channel-name → channel ID. Pass-through if already an ID."""
    if not channel.startswith("#"):
        return channel
    name = channel.lstrip("#")
    cursor = None
    while True:
        kwargs: dict = {"types": "public_channel,private_channel", "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        result = client.conversations_list(**kwargs)
        for c in result.get("channels", []):
            if c.get("name") == name:
                return c["id"]
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    raise ValueError(f"Channel not found: {channel}")


def _fetch_thread_messages(client: WebClient, channel_id: str, thread_ts: str) -> list[dict]:
    result = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=50)
    return result.get("messages", [])


def _fetch_channel_thread_roots(
    client: WebClient,
    channel_id: str,
    since_ts: Optional[str],
    limit: int = 50,
) -> list[dict]:
    """Return root messages from channel history since since_ts."""
    kwargs: dict = {"channel": channel_id, "limit": limit}
    if since_ts:
        kwargs["oldest"] = since_ts
    result = client.conversations_history(**kwargs)
    return result.get("messages", [])


def _resolve_user_names(client: WebClient, user_ids: list[str]) -> dict[str, str]:
    """Return {slack_user_id: display_name}. Best-effort — unknown IDs map to themselves."""
    mapping: dict[str, str] = {}
    for uid in set(user_ids):
        if not uid or uid in mapping:
            continue
        try:
            info = client.users_info(user=uid)
            profile = info.get("user", {}).get("profile", {})
            mapping[uid] = (
                profile.get("display_name")
                or profile.get("real_name")
                or uid
            )
        except SlackApiError:
            mapping[uid] = uid
    return mapping


def _format_thread_text(messages: list[dict], user_map: dict[str, str]) -> str:
    lines = []
    for m in messages:
        uid = m.get("user", "")
        name = user_map.get(uid, uid) or "system"
        text = (m.get("text") or "").strip()
        if text:
            lines.append(f"{name}: {text}")
    return "\n".join(lines)


# ── LLM extraction ───────────────────────────────────────────────────────────

_EXTRACTION_SYSTEM = """You are a teamwork graph extractor. Extract structured entities from a Slack thread or Canvas document.

Return only JSON — no other text:
{
  "ingest_worthy": true,
  "thread_summary": "one sentence",
  "decisions": [
    {
      "title": "...",
      "rationale": "...",
      "rejected_alternatives": ["..."],
      "made_by": "display name or slack ID",
      "confidence": "high|medium|low"
    }
  ],
  "tasks": [
    {
      "title": "...",
      "owner": "display name or slack ID",
      "due": "EOD|this week|YYYY-MM-DD|unspecified",
      "confidence": "high|medium|low"
    }
  ],
  "blockers": [
    {
      "description": "...",
      "severity": "critical|high|medium",
      "blocks_what": "short description of what is blocked",
      "confidence": "high|medium|low"
    }
  ],
  "people": ["display name or ID", ...]
}

Extraction rules:
- Only extract entities explicitly stated. Do not infer.
- Decision: requires explicit choice language ("going with X", "we decided", "final call", "approved").
- Task: requires explicit ownership or commitment ("I'll take", "assigned to", "will do by").
- Blocker: requires explicit impediment language ("blocked by", "waiting on", "can't proceed").
- confidence=high: entity is unambiguous and direct.
- confidence=medium: reasonable inference from context.
- confidence=low: speculative — omit unless clearly worth surfacing.
- Set ingest_worthy=false if no decisions, tasks, or blockers were found."""


def _call_extractor(text: str, source_label: str) -> dict:
    """Call Nemotron-Super to extract entities. Returns parsed dict or empty structure."""
    prompt = f"Source: {source_label}\n\n{text}\n\nExtract teamwork graph entities."
    raw = reason(prompt, system=_EXTRACTION_SYSTEM, model=Model.SUPER)
    parsed = parse_json(raw)
    if not parsed:
        return {
            "ingest_worthy": False, "thread_summary": "extraction failed",
            "decisions": [], "tasks": [], "blockers": [], "people": [],
        }
    return parsed


# ── Graph writes ─────────────────────────────────────────────────────────────

def _write_entities(
    extraction: dict,
    source_url: str,
    graph,
    project_root: str,
    base_epistemic_state: str = "proposed",
    ctx=None,
) -> dict[str, int]:
    """
    Write extracted entities as typed graph objects.
    Returns {type: count} of objects written.
    confidence=low entities are skipped — they feed the Regimes loop as noise.

    graph is a BehaviorGraph when called from inside a behavior (no .objects()).
    ctx must be provided when called from a behavior so person dedup can use ctx.view.
    """
    written: dict[str, int] = {"decision": 0, "task": 0, "blocker": 0, "person": 0}

    for d in extraction.get("decisions", []):
        if d.get("confidence") == "low":
            continue
        obj = graph.add_object("decision", data={
            "title":                  d.get("title", ""),
            "rationale":              d.get("rationale", ""),
            "rejected_alternatives":  d.get("rejected_alternatives", []),
            "made_by":                d.get("made_by", ""),
            "confidence":             d.get("confidence", "medium"),
            "epistemic_state":        base_epistemic_state,
            "source":                 source_url,
        })
        written["decision"] += 1
        append_event(project_root, {
            "type":        "graph.object.created",
            "object_type": "decision",
            "object_id":   obj.id,
            "title":       d.get("title", ""),
            "confidence":  d.get("confidence", "medium"),
            "source":      source_url,
        })

    for t in extraction.get("tasks", []):
        if t.get("confidence") == "low":
            continue
        obj = graph.add_object("task", data={
            "title":           t.get("title", ""),
            "owner":           t.get("owner", ""),
            "due":             t.get("due", "unspecified"),
            "status":          "open",
            "confidence":      t.get("confidence", "medium"),
            "epistemic_state": base_epistemic_state,
            "source":          source_url,
        })
        written["task"] += 1
        append_event(project_root, {
            "type":        "graph.object.created",
            "object_type": "task",
            "object_id":   obj.id,
            "title":       t.get("title", ""),
            "confidence":  t.get("confidence", "medium"),
            "source":      source_url,
        })

    for b in extraction.get("blockers", []):
        obj = graph.add_object("blocker", data={
            "description":     b.get("description", ""),
            "severity":        b.get("severity", "medium"),
            "blocks_what":     b.get("blocks_what", ""),
            "status":          "open",
            "age_days":        0,
            "confidence":      b.get("confidence", "medium"),
            "epistemic_state": base_epistemic_state,
            "source":          source_url,
        })
        written["blocker"] += 1
        append_event(project_root, {
            "type":        "graph.object.created",
            "object_type": "blocker",
            "object_id":   obj.id,
            "description": b.get("description", ""),
            "confidence":  b.get("confidence", "medium"),
            "source":      source_url,
        })

    for name_or_id in extraction.get("people", []):
        # Avoid duplicates. ctx.view.objects() works inside a behavior;
        # skip dedup when called from outside (ctx=None).
        existing = []
        if ctx is not None:
            existing = [
                o for o in ctx.view.objects(type="person")
                if o.data.get("slack_id") == name_or_id
                or o.data.get("name") == name_or_id
            ]
        if not existing:
            graph.add_object("person", data={
                "slack_id":        name_or_id if name_or_id.startswith("U") else "",
                "name":            name_or_id,
                "epistemic_state": "observed",
                "source":          source_url,
            })
            written["person"] += 1

    return written


# ── Extraction behaviors ─────────────────────────────────────────────────────

@behavior(on=["object.created"], where={"object.type": "slack_thread_raw"})
def slack_thread_extractor(event, graph, ctx):
    """Extract Decision/Task/Blocker/Person entities from an ingested Slack thread."""
    raw_id = event.payload.get("object", {}).get("id")
    if not raw_id:
        return

    raw_obj = graph.get_object(raw_id)
    if not raw_obj:
        return

    data = raw_obj.data
    thread_text = data.get("formatted_text", "")
    if not thread_text:
        return

    source_url = (
        f"slack://channel/{data.get('channel_id', '')}"
        f"/thread/{data.get('thread_ts', '')}"
    )
    extraction = _call_extractor(thread_text, source_label=source_url)

    if not extraction.get("ingest_worthy", False):
        # Still record the attempt so Regimes can track discard rate.
        append_event(data.get("project_root", ""), {
            "type":       "slack.thread.discarded",
            "reason":     extraction.get("thread_summary", "not ingest_worthy"),
            "source":     source_url,
        })
        return

    written = _write_entities(
        extraction,
        source_url=source_url,
        graph=graph,
        project_root=data.get("project_root", ""),
        base_epistemic_state="proposed",
        ctx=ctx,
    )

    # Tag the raw object as processed so Regimes can query extraction yield.
    graph.patch_object(raw_id, updates={
        "processed":      True,
        "entities_found": written,
        "summary":        extraction.get("thread_summary", ""),
    })

    # Quality signal: ingest_worthy but nothing extracted → Regimes fodder.
    if sum(written.values()) == 0:
        append_event(data.get("project_root", ""), {
            "type":     "behavior.failed",
            "behavior": "slack_thread_extractor",
            "reason":   "extraction_empty",
            "source":   source_url,
        })


@behavior(on=["object.created"], where={"object.type": "slack_canvas_raw"})
def slack_canvas_extractor(event, graph, ctx):
    """Extract entities from an ingested Slack Canvas.

    Canvas is higher-confidence than a thread: structured headings and
    checklist items are explicit signals, not conversational inference.
    Base epistemic state is 'observed' for Canvas rather than 'proposed'.
    """
    raw_id = event.payload.get("object", {}).get("id")
    if not raw_id:
        return

    raw_obj = graph.get_object(raw_id)
    if not raw_obj:
        return

    data = raw_obj.data
    canvas_text = data.get("content", "")
    if not canvas_text:
        return

    source_url = f"slack://canvas/{data.get('canvas_id', '')}"
    extraction = _call_extractor(canvas_text, source_label=source_url)

    if not extraction.get("ingest_worthy", False):
        return

    _write_entities(
        extraction,
        source_url=source_url,
        graph=graph,
        project_root=data.get("project_root", ""),
        base_epistemic_state="observed",
        ctx=ctx,
    )

    graph.patch_object(raw_id, updates={"processed": True})


# ── Runtime factory ──────────────────────────────────────────────────────────

def make_teamwork_runtime(graph: Graph, project_root: str) -> Runtime:
    """Create an ActiveGraph Runtime with both Slack extraction behaviors registered.

    The SQLite store persists the lineage at <project_root>/.teamwork.sqlite.
    Pass this runtime to SlackConnector and call runtime.run_until_idle()
    after each sweep to fire the extractors.
    """
    db = str(Path(project_root) / ".teamwork.sqlite")
    return Runtime(
        graph,
        behaviors=[slack_thread_extractor, slack_canvas_extractor],
        persist_to=db,
    )


# ── SlackConnector ───────────────────────────────────────────────────────────

class SlackConnector:
    """Fetches Slack threads and canvases and adds them to the teamwork graph.

    After calling .sweep() or .ingest_thread(), call runtime.run_until_idle()
    to fire the extraction behaviors and write typed entities to the graph.

    Args:
        project_root:     Path to the project repo (used for dedup + event log).
        graph:            ActiveGraph Graph instance shared with the Runtime.
        watched_channels: Channel names (#general) or IDs to sweep.
        min_thread_length: Minimum number of messages for a thread to qualify.
    """

    def __init__(
        self,
        project_root: str,
        graph: Graph,
        watched_channels: list[str],
        min_thread_length: int = 2,
    ) -> None:
        self.project_root = project_root
        self.graph = graph
        self.watched_channels = watched_channels
        self.min_thread_length = min_thread_length
        self._client = _make_client()
        self._channel_id_cache: dict[str, str] = {}

    def _channel_id(self, channel: str) -> str:
        if channel not in self._channel_id_cache:
            self._channel_id_cache[channel] = _resolve_channel_id(self._client, channel)
        return self._channel_id_cache[channel]

    def ingest_thread(self, channel_id: str, thread_ts: str) -> bool:
        """Fetch one thread and add a slack_thread_raw object to the graph.

        Returns True if the thread was newly ingested, False if already seen
        or did not qualify.
        """
        if _already_ingested(self.project_root, channel_id, thread_ts):
            return False

        try:
            messages = _fetch_thread_messages(self._client, channel_id, thread_ts)
        except SlackApiError as e:
            append_event(self.project_root, {
                "type":       "slack.fetch.error",
                "channel_id": channel_id,
                "thread_ts":  thread_ts,
                "error":      str(e),
            })
            return False

        if len(messages) < self.min_thread_length:
            return False

        qualifies, reason = _qualify_thread(messages)
        if not qualifies:
            return False

        # Resolve user IDs to display names for the LLM.
        user_ids = [m.get("user", "") for m in messages if m.get("user")]
        user_map = _resolve_user_names(self._client, user_ids)
        formatted = _format_thread_text(messages, user_map)

        # Add raw object — this is what triggers the extractor behavior.
        self.graph.add_object("slack_thread_raw", data={
            "channel_id":    channel_id,
            "thread_ts":     thread_ts,
            "message_count": len(messages),
            "qualify_reason": reason,
            "formatted_text": formatted,
            "project_root":  self.project_root,
            "processed":     False,
        })

        _mark_ingested(self.project_root, channel_id, thread_ts)
        append_event(self.project_root, {
            "type":          "slack.thread.ingested",
            "channel_id":    channel_id,
            "thread_ts":     thread_ts,
            "message_count": len(messages),
            "qualify_reason": reason,
        })
        return True

    def ingest_canvas(self, canvas_id: str) -> bool:
        """Fetch a Slack Canvas and add a slack_canvas_raw object to the graph.

        Returns True if newly ingested.

        Note: Canvas access requires the `files:read` scope and the canvas
        file ID (not channel ID). Obtain canvas IDs via
        client.conversations_canvases(channel=channel_id) or from the
        Slack UI URL.
        """
        if _already_ingested(self.project_root, "canvas", canvas_id):
            return False

        try:
            file_info = self._client.files_info(file=canvas_id).get("file", {})
        except SlackApiError as e:
            append_event(self.project_root, {
                "type":      "slack.fetch.error",
                "canvas_id": canvas_id,
                "error":     str(e),
            })
            return False

        # Canvas content lives in file_info["plain_text"] or "content".
        content = (
            file_info.get("plain_text")
            or file_info.get("preview")
            or file_info.get("title", "")
        )
        if not content:
            return False

        self.graph.add_object("slack_canvas_raw", data={
            "canvas_id":    canvas_id,
            "title":        file_info.get("title", ""),
            "content":      content,
            "project_root": self.project_root,
            "processed":    False,
        })

        _mark_ingested(self.project_root, "canvas", canvas_id)
        append_event(self.project_root, {
            "type":      "slack.canvas.ingested",
            "canvas_id": canvas_id,
            "title":     file_info.get("title", ""),
        })
        return True

    def sweep(self, since_ts: Optional[str] = None) -> dict:
        """Poll all watched channels for qualifying threads since since_ts.

        since_ts: Unix timestamp string (e.g. "1728000000.000"). If None,
                  fetches the 50 most recent messages per channel.

        Returns stats dict: {channel: {ingested: int, skipped: int, errors: int}}
        """
        stats: dict[str, dict[str, int]] = {}

        for channel in self.watched_channels:
            ch_stats = {"ingested": 0, "skipped": 0, "errors": 0}
            try:
                channel_id = self._channel_id(channel)
            except (ValueError, SlackApiError) as e:
                append_event(self.project_root, {
                    "type":    "slack.sweep.error",
                    "channel": channel,
                    "error":   str(e),
                })
                stats[channel] = {"ingested": 0, "skipped": 0, "errors": 1}
                continue

            try:
                roots = _fetch_channel_thread_roots(
                    self._client, channel_id, since_ts=since_ts
                )
            except SlackApiError as e:
                append_event(self.project_root, {
                    "type":       "slack.sweep.error",
                    "channel_id": channel_id,
                    "error":      str(e),
                })
                stats[channel] = {"ingested": 0, "skipped": 0, "errors": 1}
                continue

            for root in roots:
                ts = root.get("ts")
                if not ts:
                    continue
                try:
                    ingested = self.ingest_thread(channel_id, ts)
                    if ingested:
                        ch_stats["ingested"] += 1
                    else:
                        ch_stats["skipped"] += 1
                except Exception as e:
                    ch_stats["errors"] += 1
                    append_event(self.project_root, {
                        "type":       "slack.thread.error",
                        "channel_id": channel_id,
                        "thread_ts":  ts,
                        "error":      str(e),
                    })

            stats[channel] = ch_stats

        append_event(self.project_root, {
            "type":      "slack.sweep.complete",
            "since_ts":  since_ts,
            "channels":  list(stats.keys()),
            "stats":     stats,
        })
        return stats
