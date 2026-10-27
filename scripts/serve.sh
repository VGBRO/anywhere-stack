#!/bin/bash
# Start the Anywhere Stack API server (Nemotron on Nebius Token Factory)
set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

if [ ! -f ".env" ]; then
  echo "⚠  No .env file found. Copy .env.example to .env and add your NEBIUS_API_KEY."
  exit 1
fi

echo "◆ Starting Anywhere Stack API on http://localhost:8747"
echo "  Models: Nemotron NANO (routing) + Nemotron ULTRA (CoS)"
echo "  Provider: Nebius Token Factory"
echo ""

uv run uvicorn anywhere.api:app --host 0.0.0.0 --port 8747 --reload
