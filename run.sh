#!/bin/bash
# ArchiveMind - Start Script
# Run from the project root: ./run.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== ArchiveMind Startup ==="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.8+ first."
    exit 1
fi
echo "Python: $(python3 --version)"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "Starting ArchiveMind server at http://localhost:8000"
echo "Press Ctrl+C to stop."
echo ""

# Run from project root so imports work correctly
python3 -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
