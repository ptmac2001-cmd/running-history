#!/bin/bash
# Launch script for Running History app

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting backend..."
source "$PROJECT_DIR/.venv/bin/activate"
cd "$PROJECT_DIR/backend"
uvicorn main:app --reload &
BACKEND_PID=$!

echo "Starting frontend..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait a moment then open browser
sleep 3
open "http://localhost:5173"

echo "App running. Press Ctrl+C to stop."

# On exit, kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
