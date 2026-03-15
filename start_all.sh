#!/bin/bash

# --- CONFIGURATION: Set absolute paths so cd errors can't break anything ---
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend_api"
DASHBOARD_DIR="$PROJECT_ROOT/web_dashboard"
VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
VENV_STREAMLIT="$BACKEND_DIR/venv/bin/streamlit"

# --- FIX #2: Safer port cleanup that won't abort on empty results ---
echo "Cleaning up ports..."
lsof -t -i:5000 | xargs kill -9 2>/dev/null || true
lsof -t -i:8501 | xargs kill -9 2>/dev/null || true

echo "Starting Maize AI Ecosystem..."

# --- FIX #3: Validate directories exist before proceeding ---
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Error: backend_api directory not found at $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$DASHBOARD_DIR" ]; then
    echo "❌ Error: web_dashboard directory not found at $DASHBOARD_DIR"
    exit 1
fi

# Validate venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Error: Virtual environment not found. Run:"
    echo "   cd $BACKEND_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# --- FIX #1: Use venv Python/Streamlit directly for BOTH services ---
echo "Starting Flask Backend..."
cd "$BACKEND_DIR"
"$VENV_PYTHON" app.py &
BACKEND_PID=$!
echo "✅ Flask Backend running (PID: $BACKEND_PID)"

echo "Starting Streamlit Dashboard..."
cd "$DASHBOARD_DIR"
"$VENV_STREAMLIT" run app.py &
DASHBOARD_PID=$!
echo "✅ Streamlit Dashboard running (PID: $DASHBOARD_PID)"

echo ""
echo "🌾 Maize AI Ecosystem is live!"
echo "   Flask:      http://127.0.0.1:5000"
echo "   Streamlit:  http://localhost:8501"
echo "   Press Ctrl+C to stop all services."
echo ""

# --- FIX #4: Catch both SIGINT and SIGTERM to cleanly stop all processes ---
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill "$BACKEND_PID" "$DASHBOARD_PID" 2>/dev/null
    wait "$BACKEND_PID" "$DASHBOARD_PID" 2>/dev/null
    echo "✅ All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM
wait