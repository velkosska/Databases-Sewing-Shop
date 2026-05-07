#!/usr/bin/env bash
# Start Django + Next.js dev servers together.
# Usage: ./start.sh
# Ctrl+C stops both cleanly.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Kill any leftover processes on our ports ──────────────────────────────
echo "Stopping any existing servers..."
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 1

# Free ports just in case something else grabbed them
for PORT in 8000 3000; do
  PID=$(lsof -ti tcp:$PORT 2>/dev/null) || true
  if [ -n "$PID" ]; then
    echo "  Freeing port $PORT (pid $PID)..."
    kill "$PID" 2>/dev/null || true
  fi
done
sleep 1

# ── Start Django ──────────────────────────────────────────────────────────
echo "Starting Django backend on http://127.0.0.1:8000 ..."
cd "$SCRIPT_DIR"
source venv/bin/activate
python manage.py runserver 8000 &
DJANGO_PID=$!

# Give Django a moment to bind the port
sleep 2

# ── Start Next.js ─────────────────────────────────────────────────────────
echo "Starting Next.js frontend on http://localhost:3000 ..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
NEXT_PID=$!

echo ""
echo "  Backend  → http://127.0.0.1:8000"
echo "  Frontend → http://localhost:3000"
echo "  Admin    → http://127.0.0.1:8000/admin/"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$DJANGO_PID" "$NEXT_PID" 2>/dev/null || true
  # Belt-and-suspenders: also kill by process name
  pkill -f "manage.py runserver" 2>/dev/null || true
  pkill -f "next dev" 2>/dev/null || true
  exit 0
}

trap cleanup SIGINT SIGTERM
wait
