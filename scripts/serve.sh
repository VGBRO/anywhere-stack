#!/bin/bash
# Start the Anywhere Stack API server (Claude via Anthropic API)
set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

echo "Starting Anywhere Stack FastAPI (PORT defaults to 8080)"
echo "  Models: Claude Haiku (routing) + Claude Opus (CoS)
echo "  Provider: Anthropic"
echo ""

exec uv run python artifacts/api-server/main.py
