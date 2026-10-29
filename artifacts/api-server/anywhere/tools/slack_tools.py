"""Slack tools — discover channels, read history, post messages."""

from __future__ import annotations

import json
import os
from slack_sdk import WebClient


def _client() -> WebClient:
    return WebClient(token=os.environ.get("SLACK_BOT_TOKEN", ""))


def search_channels(query: str, limit: int = 20) -> str:
    """Find channels whose name contains the query string."""
    try:
        all_channels = []
        cursor = None
        while True:
            kwargs = {"types": "public_channel,private_channel", "limit": 200, "exclude_archived": True}
            if cursor:
                kwargs["cursor"] = cursor
            result = _client().conversations_list(**kwargs)
            all_channels.extend(result.get("channels", []))
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        q = query.lower()
        matches = [c for c in all_channels if q in c.get("name", "").lower()][:limit]
        if not matches:
            return f"No channels found matching '{query}'."
        return json.dumps([{"id": c["id"], "name": c["name"], "topic": c.get("topic", {}).get("value", "")} for c in matches], indent=2)
    except Exception as e:
        return f"Error searching channels: {e}"


def read_channel(channel: str, limit: int = 20) -> str:
    """Read recent messages from a channel (name like #general or channel ID)."""
    try:
        # Resolve channel name to ID if needed
        if channel.startswith("#"):
            resolved = _resolve_channel_name(channel.lstrip("#"))
            if resolved:
                channel = resolved
        result = _client().conversations_history(channel=channel, limit=min(limit, 50))
        messages = result.get("messages", [])
        lines = []
        for m in reversed(messages):
            user = m.get("user", "bot")
            text = (m.get("text") or "").replace("\n", " ")[:300]
            lines.append(f"{user}: {text}")
        return "\n".join(lines) if lines else "No messages found."
    except Exception as e:
        return f"Error reading channel: {e}"


def post_message(channel: str, text: str) -> str:
    try:
        _client().chat_postMessage(channel=channel, text=text)
        return f"Posted to {channel}."
    except Exception as e:
        return f"Error posting: {e}"


def search_messages(query: str, channel: str = None, limit: int = 20) -> str:
    """Search message content across the workspace (requires search:read scopes + user token)."""
    try:
        kwargs = {"query": query, "count": min(limit, 20)}
        if channel:
            kwargs["query"] = f"in:{channel} {query}"
        result = _client().search_messages(**kwargs)
        matches = result.get("messages", {}).get("matches", [])
        if not matches:
            return f"No messages found for '{query}'."
        lines = []
        for m in matches:
            ch = m.get("channel", {}).get("name", "?")
            user = m.get("username", m.get("user", "?"))
            text = (m.get("text") or "").replace("\n", " ")[:300]
            lines.append(f"#{ch} | {user}: {text}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching messages: {e}"


def _resolve_channel_name(name: str) -> str | None:
    """Resolve a channel name to its ID."""
    try:
        cursor = None
        while True:
            kwargs = {"types": "public_channel,private_channel", "limit": 200}
            if cursor:
                kwargs["cursor"] = cursor
            result = _client().conversations_list(**kwargs)
            for c in result.get("channels", []):
                if c.get("name") == name:
                    return c["id"]
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except Exception:
        pass
    return None
