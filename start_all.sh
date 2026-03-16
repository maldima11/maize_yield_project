#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend_api"
DASHBOARD_DIR="$PROJECT_ROOT/web_dashboard"
VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
VENV_STREAMLIT="$BACKEND_DIR/venv/bin/streamlit"

echo "🚀 Starting Maize Yield System..."

# ── Validation ───────────────────────────────
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Error: backend_api not found at $BACKEND_DIR"; exit 1
fi
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo "❌ Error: web_dashboard not found at $DASHBOARD_DIR"; exit 1
fi
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found. Run:"
    echo "   cd $BACKEND_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# ── Clean up ports ────────────────────────────
echo "🧹 Cleaning up ports 5000 and 8501..."
lsof -t -i:5000 | xargs kill -9 2>/dev/null || true
lsof -t -i:8501 | xargs kill -9 2>/dev/null || true
sleep 1

# ── 1. Start Flask ────────────────────────────
echo "📡 Starting Flask Backend..."
cd "$BACKEND_DIR"
"$VENV_PYTHON" app.py &
BACKEND_PID=$!
echo "✅ Flask running (PID: $BACKEND_PID)"
sleep 3

# ── 2. Start Streamlit ────────────────────────
echo "🎨 Starting Streamlit Dashboard..."
cd "$DASHBOARD_DIR"
"$VENV_STREAMLIT" run app.py --server.port 8501 &
STREAMLIT_PID=$!
echo "✅ Streamlit running (PID: $STREAMLIT_PID)"
sleep 2

# ── 3. Start Serveo tunnel ────────────────────
echo "🌐 Starting Serveo tunnel (keepalive enabled)..."
ssh -o ServerAliveInterval=60 \
    -o StrictHostKeyChecking=no \
    -R 80:localhost:5000 serveo.net &
SERVEO_PID=$!
echo "✅ Serveo tunnel started (PID: $SERVEO_PID)"

echo ""
echo "=============================================="
echo "✅ All services are running!"
echo ""
echo "   Flask API:  http://127.0.0.1:5000"
echo "   Dashboard:  http://localhost:8501"
echo ""
echo "   USSD Tunnel: Wait ~5 seconds then check"
echo "   above output for your Serveo URL, e.g.:"
echo "   https://xxxxxxxx.serveousercontent.com"
echo ""
echo "   Then set AT callback URL to:"
echo "   https://gyroscopic-cristiano-unpanicky.ngrok-free.dev/ussd"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all services."

# ── Cleanup on exit ───────────────────────────
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID $STREAMLIT_PID $SERVEO_PID 2>/dev/null
    wait $BACKEND_PID $STREAMLIT_PID $SERVEO_PID 2>/dev/null
    echo "✅ All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM
wait