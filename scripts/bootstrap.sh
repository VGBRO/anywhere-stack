#!/usr/bin/env bash
# Bootstrap the Anywhere Stack on a fresh machine.
set -e

echo "=== Anywhere Stack Bootstrap ==="
echo ""

# Check Python 3.11+
python3 --version 2>/dev/null || { echo "ERROR: Python 3.11+ required"; exit 1; }
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python $PYTHON_VERSION"

# Check uv (preferred) or pip
if command -v uv &>/dev/null; then
    echo "✓ uv found"
    INSTALLER="uv"
else
    echo "  uv not found — using pip (install uv for faster setup: https://docs.astral.sh/uv/)"
    INSTALLER="pip"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
if [ "$INSTALLER" = "uv" ]; then
    uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e .
else
    pip install -e .
fi
echo "✓ Dependencies installed"

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "✓ Created .env from .env.example"
    echo "  → Edit .env and add your NEBIUS_API_KEY and Slack tokens"
else
    echo "✓ .env already exists"
fi

# Verify Nebius connection
echo ""
echo "Testing Nebius connection..."
if python3 -c "from anywhere.client import get_client; get_client()" 2>/dev/null; then
    anywhere test-nebius 2>/dev/null || echo "  (run 'anywhere test-nebius' after setting NEBIUS_API_KEY)"
else
    echo "  → Set NEBIUS_API_KEY in .env then run: anywhere test-nebius"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: anywhere test-nebius"
echo "  3. Run: anywhere heartbeat example-project"
echo "  4. Run: anywhere slack  (to start the Slack listener)"
echo ""
echo "Docs: see README.md"
