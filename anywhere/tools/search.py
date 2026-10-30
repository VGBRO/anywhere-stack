"""Tavily web search tool — real-time research for agent tasks."""

import os
import json
import httpx


def web_search(query: str, max_results: int = 5) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Web search unavailable: TAVILY_API_KEY not configured."

    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": True,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return f"Search failed: {e}"

    lines = []
    answer = data.get("answer")
    if answer:
        lines.append(f"Summary: {answer}\n")

    for r in data.get("results", [])[:max_results]:
        snippet = r.get("content", "")[:250].replace("\n", " ")
        lines.append(f"- {r['title']}\n  {r['url']}\n  {snippet}")

    return "\n".join(lines) if lines else "No results found."
