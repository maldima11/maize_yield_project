#!/bin/bash

# Kill any existing processes on ports 5000 and 8501
echo "Cleaning up ports..."
kill -9 $(lsof -t -i:5000) 2>/dev/null
kill -9 $(lsof -t -i:8501) 2>/dev/null

echo "Starting Maize AI Ecosystem..."

# 1. Start Flask Backend
cd backend_api
source venv/bin/activate
python app.py & 
BACKEND_PID=$!
echo "✅ Flask Backend running (PID: $BACKEND_PID)"

# 2. Start Streamlit Dashboard
cd ../web_dashboard
streamlit run app.py &
DASHBOARD_PID=$!
echo "✅ Streamlit Dashboard running (PID: $DASHBOARD_PID)"

# Handle script shutdown
trap "kill $BACKEND_PID $DASHBOARD_PID; echo 'Stopping servers...'; exit" SIGINT
wait