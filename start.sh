#!/bin/bash

echo "🚀 Booting up Trackly AI..."

# 1. Start the Python Backend
echo "-> Starting FastAPI Backend (Port 8000)..."
cd backend
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 2. Start the React Frontend
echo "-> Starting Vite Frontend (Port 5174)..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 5174 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All servers are running!"
echo "🌐 You can access the app at: http://localhost:5174"
echo "🛑 Press Ctrl+C at any time to gracefully shut down both servers."
echo ""

# Catch the Ctrl+C signal so it kills both servers at once
trap "echo -e '\n🛑 Shutting down servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

# Keep the script running
wait $BACKEND_PID
wait $FRONTEND_PID
