#!/usr/bin/env bash
# ==============================================================================
# Autism Lens — Direct Startup Script (Linux / macOS)
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================================="
echo "  🩺 Autism Lens — Clinical Decision Support System"
echo "  Official Pearson VABS-3 & DSM-5-TR Decision Support"
echo "=================================================================="

# Detect Python interpreter
if [ -f "$DIR/.venv/bin/python" ]; then
    PYTHON_EXEC="$DIR/.venv/bin/python"
elif [ -f "/home/talha/.venv/bin/python" ]; then
    PYTHON_EXEC="/home/talha/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_EXEC="python3"
else
    echo "[ERROR] Python 3 not found. Please install Python 3.10+."
    exit 1
fi

echo "[*] Using Python: $PYTHON_EXEC"
echo "[*] Starting Autism Lens application..."
echo "[*] Your browser will open at http://127.0.0.1:5050"
echo ""

export PYTHONPATH="$DIR"
exec "$PYTHON_EXEC" "$DIR/run.py"
