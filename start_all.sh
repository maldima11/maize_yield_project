#!/bin/bash

# Get the absolute path of the project directory
PROJECT_DIR="/Users/mac/Documents/maize_yield_project"

echo "🚀 Starting Maize Yield System..."

# 1. Activate Environment
source "$PROJECT_DIR/venv/bin/activate"

# 2. Start Flask Backend in the background
echo "📡 Starting Flask Backend..."
cd "$PROJECT_DIR/backend_api"
python3 app.py &
BACKEND_PID=$!

# Wait a moment for Flask to warm up
sleep 3

# 3. Start Streamlit Dashboard
echo "🎨 Starting Streamlit Dashboard..."
cd "$PROJECT_DIR/web_dashboard"
streamlit run app.py --server.port 8501 &
STREAMLIT_PID=$!

echo "✅ System is running!"
echo "Backend PID: $BACKEND_PID"
echo "Streamlit PID: $STREAMLIT_PID"
echo "Press Ctrl+C to stop both."

# Keep script running to catch Ctrl+C
trap "kill $BACKEND_PID $STREAMLIT_PID; exit" INT
wait