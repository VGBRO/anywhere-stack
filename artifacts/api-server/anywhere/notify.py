"""Lightweight outbound notification — no Slack Bolt dependency.

Avoids circular imports: cos.py → notify.py is safe; slack.py → cos.py also safe.
All calls are best-effort and never raise.
"""

from __future__ import annotations
import os
import requests
from dotenv import load_dotenv

load_dotenv()

_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
_CHANNEL = os.getenv("COS_SLACK_CHANNEL", "#anywhere-stack")


def post_to_slack(message: str, channel: str | None = None) -> bool:
    """Post a plain-text message to Slack. Returns True on success."""
    if not _BOT_TOKEN:
        return False
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {_BOT_TOKEN}", "Content-Type": "application/json"},
            json={"channel": channel or _CHANNEL, "text": message},
            timeout=5,
        )
        return resp.ok and resp.json().get("ok", False)
    except Exception:
        return False
