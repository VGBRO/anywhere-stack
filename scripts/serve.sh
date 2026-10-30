#!/bin/bash
# Start the Anywhere Stack API server (Nemotron on Nebius Token Factory)
set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

echo "Starting Anywhere Stack FastAPI (PORT defaults to 8080)"
echo "  Models: Nemotron NANO (routing) + Nemotron ULTRA (CoS)"
echo "  Provider: Nebius Token Factory"
echo ""

exec uv run python artifacts/api-server/main.py
