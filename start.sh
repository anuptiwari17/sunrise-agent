#!/usr/bin/env bash
# Start both backend and frontend concurrently
set -e

echo "Starting Sunrise Clinic Backend & Frontend..."

python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cd frontend
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
