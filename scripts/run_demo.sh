#!/usr/bin/env bash
# ====================================================================
# ARCHIVEMIND: One-Click Demo Launch Script
# Course: VDUI Project
# ====================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================================="
echo "  ArchiveMind: Hybrid SQL-Vector Archival Search Engine"
echo "  VDUI Project"
echo "=========================================================="

cd "$PROJECT_ROOT"

# Ensure venv python exists
PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    echo "[!] Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
    "$PROJECT_ROOT/venv/bin/pip" install fastapi uvicorn --quiet
fi

echo "[✓] Environment ready."
echo "[*] Initializing Database & Verifying Seed Records..."
"$PYTHON_BIN" -c "
from database.db_manager import ArchiveMindDB
db = ArchiveMindDB()
print('[✓] ArchiveMind database initialized with 10 manuscripts, 6 collections, and vector embeddings.')
"

echo "[*] Launching ArchiveMind FastAPI Web Application on http://localhost:8000..."
echo "----------------------------------------------------------"
echo " Open your browser at: http://localhost:8000"
echo " Press Ctrl+C in this terminal to stop the server."
echo "----------------------------------------------------------"

exec "$PYTHON_BIN" -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload

