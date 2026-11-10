"""GitHub tools — discover repos, read files, list issues."""

import base64
import json
import os
import requests

_BASE = "https://api.github.com"
_GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
_GITHUB_USER = os.getenv("GITHUB_ORG", os.getenv("GITHUB_USER", ""))


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if _GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {_GITHUB_TOKEN}"
    return h


def _full_repo(repo: str) -> str:
    if "/" not in repo:
        return f"{_GITHUB_USER}/{repo}"
    return repo


def list_my_repos() -> str:
    """List all repos owned by the configured GitHub user."""
    url = f"{_BASE}/users/{_GITHUB_USER}/repos?per_page=50&sort=pushed"
    r = requests.get(url, headers=_headers(), timeout=10)
    if not r.ok:
        return f"GitHub error {r.status_code}: {r.text[:200]}"
    repos = [
        {"name": repo["name"], "full_name": repo["full_name"], "open_issues": repo["open_issues_count"]}
        for repo in r.json()
        if not repo["fork"]
    ]
    return json.dumps(repos, indent=2) if repos else "No repos found."


def read_file(repo: str, path: str, ref: str = "main") -> str:
    url = f"{_BASE}/repos/{_full_repo(repo)}/contents/{path}?ref={ref}"
    r = requests.get(url, headers=_headers(), timeout=10)
    if not r.ok:
        return f"GitHub error {r.status_code}: {r.text[:200]}"
    data = r.json()
    if data.get("encoding") != "base64":
        return f"Unexpected encoding: {data.get('encoding')}"
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def list_issues(repo: str, state: str = "open") -> str:
    url = f"{_BASE}/repos/{_full_repo(repo)}/issues?state={state}&per_page=20"
    r = requests.get(url, headers=_headers(), timeout=10)
    if not r.ok:
        return f"GitHub error {r.status_code}: {r.text[:200]}"
    issues = [
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"],
            "labels": [lb["name"] for lb in i.get("labels", [])],
        }
        for i in r.json()
        if "pull_request" not in i
    ]
    return json.dumps(issues, indent=2) if issues else "No issues found."
