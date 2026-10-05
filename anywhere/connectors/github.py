"""GitHub PR connector for the Teamwork Graph.

PRs are the highest-confidence source: they are deterministic. No LLM needed
for the core signals. The behavior writes objects with epistemic_state=observed.

Deterministic signals (observed):
  PR opened            → task   (owner=author, status=open)
  PR merged            → outcome (evidence=PR URL)
  PR labeled "blocked" → blocker (severity=high)
  PR author/reviewers  → person

Cross-source linking (observed, high value):
  Merged PR outcome → search existing tasks by title overlap → task.produces.outcome
  This is what validates Slack extractions with real delivered work.

LLM signals (proposed, optional):
  PR body contains decision language → decision object
  Only fires when NEBIUS_API_KEY is set and body is non-trivial.

Public API:
  GitHubConnector(project_root, graph, watched_repos)
    .sweep(since_iso)     poll all watched repos for PRs since a timestamp
    .ingest_pr(repo, n)   fetch + add one PR; returns True if new

  github_pr_extractor     behavior — fires on github_pr_raw objects
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

import requests

from activegraph import Graph, Runtime
from activegraph.behaviors.decorators import behavior

from anywhere.state.canonical import append_event, parse_json


# ── GitHub REST helpers ──────────────────────────────────────────────────────

_BASE = "https://api.github.com"
_BLOCKED_LABELS = {"blocked", "on hold", "waiting", "do not merge"}
_DECISION_MARKERS = [
    "decided to", "going with", "we chose", "final decision",
    "we will use", "approved approach",
]

_DEDUPE_FILE = ".github_ingested.json"


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN", "")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(url: str) -> dict | list | None:
    r = requests.get(url, headers=_headers(), timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def _full_repo(repo: str) -> str:
    if "/" not in repo:
        owner = os.getenv("GITHUB_ORG", os.getenv("GITHUB_USER", "VGBRO"))
        return f"{owner}/{repo}"
    return repo


def _fetch_pr(repo: str, number: int) -> dict | None:
    return _get(f"{_BASE}/repos/{_full_repo(repo)}/pulls/{number}")


def _fetch_recent_prs(
    repo: str,
    state: str = "all",
    since_iso: Optional[str] = None,
    per_page: int = 50,
) -> list[dict]:
    """Return PR list sorted by updated_at descending."""
    url = f"{_BASE}/repos/{_full_repo(repo)}/pulls?state={state}&per_page={per_page}&sort=updated&direction=desc"
    result = _get(url)
    if not isinstance(result, list):
        return []
    if since_iso:
        result = [pr for pr in result if (pr.get("updated_at") or "") >= since_iso]
    return result


def _fetch_pr_reviews(repo: str, number: int) -> list[dict]:
    result = _get(f"{_BASE}/repos/{_full_repo(repo)}/pulls/{number}/reviews")
    return result if isinstance(result, list) else []


# ── Deduplication ────────────────────────────────────────────────────────────

def _load_dedupe(project_root: str) -> dict:
    path = Path(project_root) / _DEDUPE_FILE
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def _already_ingested(project_root: str, repo: str, pr_number: int) -> bool:
    return str(pr_number) in _load_dedupe(project_root).get(repo, [])


def _mark_ingested(project_root: str, repo: str, pr_number: int) -> None:
    store = _load_dedupe(project_root)
    store.setdefault(repo, [])
    key = str(pr_number)
    if key not in store[repo]:
        store[repo].append(key)
    (Path(project_root) / _DEDUPE_FILE).write_text(json.dumps(store, indent=2))


# ── Signal helpers ───────────────────────────────────────────────────────────

def _is_blocked(pr: dict) -> bool:
    labels = {lb["name"].lower() for lb in pr.get("labels", [])}
    return bool(labels & _BLOCKED_LABELS)


def _is_merged(pr: dict) -> bool:
    return bool(pr.get("merged") or pr.get("merged_at"))


def _has_decision_language(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in _DECISION_MARKERS)


def _title_token_overlap(a: str, b: str) -> float:
    """Return fraction of tokens in `a` that appear in `b`. Simple but fast."""
    tokens_a = set(re.findall(r'\w+', a.lower())) - {"the", "a", "an", "and", "or", "for", "to", "in", "of"}
    tokens_b = set(re.findall(r'\w+', b.lower()))
    if not tokens_a:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a)


# ── LLM extraction (optional — only for PR body decision parsing) ─────────────

_DECISION_EXTRACT_SYSTEM = """Extract a decision from this GitHub PR description if one is explicitly stated.

Return JSON only:
{
  "found": true/false,
  "title": "short decision title",
  "rationale": "why this choice was made",
  "rejected_alternatives": ["..."],
  "confidence": "high|medium|low"
}

Only extract if the description contains explicit decision language ("decided to", "going with X",
"we chose", "approved approach"). Return found=false otherwise."""


def _try_extract_decision(pr_title: str, pr_body: str, source_url: str) -> Optional[dict]:
    """Try to extract a decision from a PR body. Returns None if not applicable."""
    if not pr_body or not _has_decision_language(pr_body):
        return None
    try:
        from anywhere.client import reason, Model
        prompt = f"PR title: {pr_title}\n\nPR description:\n{pr_body[:2000]}"
        raw = reason(prompt, system=_DECISION_EXTRACT_SYSTEM, model=Model.SUPER)
        parsed = parse_json(raw)
        if parsed and parsed.get("found"):
            return parsed
    except Exception:
        pass
    return None


# ── Behavior ─────────────────────────────────────────────────────────────────

@behavior(on=["object.created"], where={"object.type": "github_pr_raw"})
def github_pr_extractor(event, graph, ctx):
    """Write deterministic teamwork entities from an ingested GitHub PR.

    Does not require an LLM for the core signals. PR state is ground truth.
    LLM is called optionally for decision extraction from PR body.
    """
    raw_id = event.payload.get("object", {}).get("id")
    if not raw_id:
        return

    raw_obj = graph.get_object(raw_id)
    if not raw_obj:
        return

    data = raw_obj.data
    source_url = data.get("source_url", "")
    project_root = data.get("project_root", "")
    written: dict[str, int] = {"task": 0, "outcome": 0, "blocker": 0, "person": 0, "decision": 0}

    # ── Person: author ────────────────────────────────────────────────────────
    author_login = data.get("author_login", "")
    if author_login:
        existing_authors = [
            o for o in ctx.view.objects(type="person")
            if o.data.get("github_login") == author_login
        ]
        if not existing_authors:
            graph.add_object("person", data={
                "github_login":    author_login,
                "name":            author_login,
                "epistemic_state": "observed",
                "source":          source_url,
            })
            written["person"] += 1

    # ── Person: reviewers ─────────────────────────────────────────────────────
    for reviewer in data.get("reviewers", []):
        existing = [
            o for o in ctx.view.objects(type="person")
            if o.data.get("github_login") == reviewer
        ]
        if not existing:
            graph.add_object("person", data={
                "github_login":    reviewer,
                "name":            reviewer,
                "epistemic_state": "observed",
                "source":          source_url,
            })
            written["person"] += 1

    # ── Task: PR opened ───────────────────────────────────────────────────────
    # A PR is a bounded unit of work. State is deterministic.
    task_status = "done" if data.get("is_merged") else (
        "open" if data.get("pr_state") == "open" else "closed"
    )
    task_obj = graph.add_object("task", data={
        "title":           data.get("title", ""),
        "owner":           author_login,
        "status":          task_status,
        "pr_number":       data.get("pr_number"),
        "repo":            data.get("repo", ""),
        "confidence":      "high",
        "epistemic_state": "observed",
        "source":          source_url,
    })
    written["task"] += 1
    append_event(project_root, {
        "type":        "graph.object.created",
        "object_type": "task",
        "object_id":   task_obj.id,
        "title":       data.get("title", ""),
        "confidence":  "high",
        "source":      source_url,
    })

    # ── Outcome: PR merged ────────────────────────────────────────────────────
    outcome_obj = None
    if data.get("is_merged"):
        outcome_obj = graph.add_object("outcome", data={
            "result":          f"PR merged: {data.get('title', '')}",
            "evidence":        source_url,
            "merged_at":       data.get("merged_at", ""),
            "confidence":      "high",
            "epistemic_state": "observed",
            "source":          source_url,
        })
        # task → produces → outcome
        graph.add_relation(task_obj.id, outcome_obj.id, "produces")
        written["outcome"] += 1
        append_event(project_root, {
            "type":        "graph.object.created",
            "object_type": "outcome",
            "object_id":   outcome_obj.id,
            "result":      f"PR merged: {data.get('title', '')}",
            "confidence":  "high",
            "source":      source_url,
        })

        # ── Cross-source link: merged PR → existing Slack task ─────────────
        # If a Slack-extracted task has title overlap ≥ 0.6 with this PR,
        # link them. This is the key cross-source validation signal.
        pr_title = data.get("title", "")
        for existing_task in ctx.view.objects(type="task"):
            if existing_task.id == task_obj.id:
                continue
            if existing_task.data.get("source", "").startswith("slack://"):
                overlap = _title_token_overlap(
                    existing_task.data.get("title", ""), pr_title
                )
                if overlap >= 0.6:
                    graph.add_relation(existing_task.id, outcome_obj.id, "validated_by")
                    append_event(project_root, {
                        "type":           "graph.cross_source.link",
                        "from_type":      "task",
                        "from_id":        existing_task.id,
                        "to_type":        "outcome",
                        "to_id":          outcome_obj.id,
                        "relation":       "validated_by",
                        "overlap_score":  overlap,
                        "note":           "slack task validated by github pr merge",
                    })

    # ── Blocker: PR labeled "blocked" ─────────────────────────────────────────
    if data.get("is_blocked"):
        blocker_obj = graph.add_object("blocker", data={
            "description":     f"PR blocked: {data.get('title', '')}",
            "severity":        "high",
            "blocks_what":     data.get("title", ""),
            "status":          "open",
            "age_days":        0,
            "confidence":      "high",
            "epistemic_state": "observed",
            "source":          source_url,
        })
        graph.add_relation(task_obj.id, blocker_obj.id, "blocked_by")
        written["blocker"] += 1
        append_event(project_root, {
            "type":        "graph.object.created",
            "object_type": "blocker",
            "object_id":   blocker_obj.id,
            "description": f"PR blocked: {data.get('title', '')}",
            "confidence":  "high",
            "source":      source_url,
        })

    # ── Decision: LLM extraction from PR body (optional) ─────────────────────
    decision = _try_extract_decision(
        data.get("title", ""), data.get("body", ""), source_url
    )
    if decision:
        dec_obj = graph.add_object("decision", data={
            "title":                 decision.get("title", ""),
            "rationale":             decision.get("rationale", ""),
            "rejected_alternatives": decision.get("rejected_alternatives", []),
            "made_by":               author_login,
            "confidence":            decision.get("confidence", "medium"),
            "epistemic_state":       "proposed",
            "source":                source_url,
        })
        written["decision"] += 1
        append_event(project_root, {
            "type":        "graph.object.created",
            "object_type": "decision",
            "object_id":   dec_obj.id,
            "title":       decision.get("title", ""),
            "confidence":  decision.get("confidence", "medium"),
            "source":      source_url,
        })

    graph.patch_object(raw_id, updates={
        "processed":      True,
        "entities_found": written,
    })


# ── GitHubConnector ───────────────────────────────────────────────────────────

class GitHubConnector:
    """Fetches GitHub PRs and adds them as raw objects to the teamwork graph.

    After calling .sweep() or .ingest_pr(), call runtime.run_until_idle()
    to fire github_pr_extractor and write typed entities.

    Args:
        project_root:   Path to the project repo (dedup + event log).
        graph:          ActiveGraph Graph instance shared with the Runtime.
        watched_repos:  Repo names ("owner/repo" or bare "repo" using GITHUB_ORG).
    """

    def __init__(
        self,
        project_root: str,
        graph: Graph,
        watched_repos: list[str],
    ) -> None:
        self.project_root = project_root
        self.graph = graph
        self.watched_repos = watched_repos

    def ingest_pr(self, repo: str, pr_number: int) -> bool:
        """Fetch one PR and add a github_pr_raw object to the graph.

        Returns True if newly ingested.
        """
        full_repo = _full_repo(repo)
        if _already_ingested(self.project_root, full_repo, pr_number):
            return False

        try:
            pr = _fetch_pr(repo, pr_number)
        except requests.HTTPError as e:
            append_event(self.project_root, {
                "type":      "github.fetch.error",
                "repo":      full_repo,
                "pr_number": pr_number,
                "error":     str(e),
            })
            return False

        if pr is None:
            return False

        reviews = []
        try:
            reviews = _fetch_pr_reviews(repo, pr_number)
        except Exception:
            pass

        reviewer_logins = list({
            r["user"]["login"]
            for r in reviews
            if r.get("user") and r["user"].get("login")
        })

        source_url = pr.get("html_url", f"https://github.com/{full_repo}/pull/{pr_number}")

        self.graph.add_object("github_pr_raw", data={
            "repo":           full_repo,
            "pr_number":      pr_number,
            "title":          pr.get("title", ""),
            "body":           (pr.get("body") or "")[:4000],   # cap for LLM
            "pr_state":       pr.get("state", "open"),
            "is_merged":      _is_merged(pr),
            "is_blocked":     _is_blocked(pr),
            "merged_at":      pr.get("merged_at", ""),
            "author_login":   (pr.get("user") or {}).get("login", ""),
            "reviewers":      reviewer_logins,
            "labels":         [lb["name"] for lb in pr.get("labels", [])],
            "source_url":     source_url,
            "project_root":   self.project_root,
            "processed":      False,
        })

        _mark_ingested(self.project_root, full_repo, pr_number)
        append_event(self.project_root, {
            "type":      "github.pr.ingested",
            "repo":      full_repo,
            "pr_number": pr_number,
            "title":     pr.get("title", ""),
            "is_merged": _is_merged(pr),
            "is_blocked": _is_blocked(pr),
        })
        return True

    def sweep(self, since_iso: Optional[str] = None) -> dict:
        """Poll all watched repos for PRs updated since since_iso.

        since_iso: ISO 8601 string (e.g. "2026-10-01T00:00:00Z"). If None,
                   fetches the 50 most recently updated PRs per repo.

        Returns stats: {repo: {ingested: int, skipped: int, errors: int}}
        """
        stats: dict[str, dict[str, int]] = {}

        for repo in self.watched_repos:
            full_repo = _full_repo(repo)
            ch_stats = {"ingested": 0, "skipped": 0, "errors": 0}

            try:
                prs = _fetch_recent_prs(repo, state="all", since_iso=since_iso)
            except Exception as e:
                append_event(self.project_root, {
                    "type":  "github.sweep.error",
                    "repo":  full_repo,
                    "error": str(e),
                })
                stats[full_repo] = {"ingested": 0, "skipped": 0, "errors": 1}
                continue

            for pr in prs:
                pr_number = pr.get("number")
                if not pr_number:
                    continue
                try:
                    ingested = self.ingest_pr(repo, pr_number)
                    if ingested:
                        ch_stats["ingested"] += 1
                    else:
                        ch_stats["skipped"] += 1
                except Exception as e:
                    ch_stats["errors"] += 1
                    append_event(self.project_root, {
                        "type":      "github.pr.error",
                        "repo":      full_repo,
                        "pr_number": pr_number,
                        "error":     str(e),
                    })

            stats[full_repo] = ch_stats

        append_event(self.project_root, {
            "type":     "github.sweep.complete",
            "since":    since_iso,
            "repos":    list(stats.keys()),
            "stats":    stats,
        })
        return stats
