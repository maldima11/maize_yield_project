#!/bin/bash

# Get the absolute path of the project directory
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend_api"
DASHBOARD_DIR="$PROJECT_ROOT/web_dashboard"
VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
VENV_STREAMLIT="$BACKEND_DIR/venv/bin/streamlit"

echo "🚀 Starting Maize Yield System..."

# --- VALIDATION: Check directories and venv exist ---
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Error: backend_api directory not found at $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$DASHBOARD_DIR" ]; then
    echo "❌ Error: web_dashboard directory not found at $DASHBOARD_DIR"
    exit 1
fi

if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Error: Virtual environment not found. Run:"
    echo "   cd $BACKEND_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# --- Cleanup ports before starting ---
echo "🧹 Cleaning up ports..."
lsof -t -i:5000 | xargs kill -9 2>/dev/null || true
lsof -t -i:8501 | xargs kill -9 2>/dev/null || true

# 1. Start Flask Backend
echo "📡 Starting Flask Backend..."
cd "$BACKEND_DIR"
"$VENV_PYTHON" app.py &
BACKEND_PID=$!
echo "✅ Flask running (PID: $BACKEND_PID)"

# Wait for Flask to warm up before starting other services
sleep 3

# 2. Start Streamlit Dashboard
echo "🎨 Starting Streamlit Dashboard..."
cd "$DASHBOARD_DIR"
"$VENV_STREAMLIT" run app.py --server.port 8501 &
STREAMLIT_PID=$!
echo "✅ Streamlit Dashboard running (PID: $STREAMLIT_PID)"

# 3. Start Serveo Tunnel with keepalive
echo "🌐 Starting Serveo tunnel..."
ssh -o ServerAliveInterval=60 -R 80:localhost:5000 serveo.net &
SERVEO_PID=$!
echo "✅ Serveo tunnel started (PID: $SERVEO_PID)"

echo ""
echo "=============================================="
echo "✅ System is fully running!"
echo "   Flask:      http://127.0.0.1:5000"
echo "   Streamlit:  http://localhost:8501"
echo "   USSD:       Check Serveo URL above, then"
echo "               update AT callback URL to:"
echo "               https://YOUR-SERVEO-URL.serveousercontent.com/ussd"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all services."

# --- Cleanup function: stops all 3 services on exit ---
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