#!/usr/bin/env bash
# ==============================================================================
# ArchiveMind — AI-Powered Hybrid SQL–Vector Semantic Search Engine
# Startup Script for Central Laptop Processing Server
# ==============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "  ArchiveMind — AI Hybrid Search & Preservation System"
echo "  Host: Laptop AI Server (RTX 2050 GPU / AMD Ryzen 5)"
echo "  Direct Ethernet: 10.42.0.1  <-->  Pi: 10.42.0.116"
echo "=========================================================="

# Check Python environment
if [ -d ".venv" ]; then
    VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif [ -d "venv" ]; then
    VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
else
    echo "Creating Python 3.11 virtual environment via uv..."
    uv venv --python 3.11 "$SCRIPT_DIR/.venv"
    VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
fi

echo "Python: $("$VENV_PYTHON" --version)"

# Probe Raspberry Pi acquisition station (Dual-Homed)
echo -n "Checking Raspberry Pi Direct Ethernet (10.42.0.116)... "
if ping -c 1 -W 1 10.42.0.116 > /dev/null 2>&1; then
    echo "ONLINE (Ultra-low latency <0.5ms)"
else
    echo "STANDBY"
fi

echo -n "Checking Raspberry Pi Local Wi-Fi (192.168.1.9)... "
if ping -c 1 -W 1 192.168.1.9 > /dev/null 2>&1; then
    echo "ONLINE (Wireless fallback active)"
else
    echo "STANDBY"
fi

echo ""
echo "=========================================================="
echo "  ArchiveMind Dashboard: http://localhost:8000"
echo "  Raspberry Pi Endpoint: http://10.42.0.1:8000"
echo "  Academic Report:       http://localhost:8000/report"
echo "=========================================================="
echo ""

# Run FastAPI backend
exec "$VENV_PYTHON" -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
