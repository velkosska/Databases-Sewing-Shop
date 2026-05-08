#!/usr/bin/env bash
# Start Django + Next.js dev servers together.
# Usage: ./start.sh
# Ctrl+C stops both cleanly.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Match config/settings.py defaults (override with env: DB_NAME, DB_USER, …)
export DB_NAME="${DB_NAME:-sewing_shop}"
export DB_USER="${DB_USER:-sewing_user}"
export DB_PASSWORD="${DB_PASSWORD:-Sewing@1234}"
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-3306}"

bootstrap_mysql() {
  if ! command -v mysql >/dev/null 2>&1; then
    echo "  (mysql client not found — skip auto-create DB; install mysql-client or create DB manually)"
    return 0
  fi
  if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" \
    -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null; then
    echo "  MySQL database '$DB_NAME' is available."
    return 0
  fi
  echo ""
  echo "  Could not create database '$DB_NAME' (missing privilege or wrong credentials)."
  echo "  Fix one of:"
  echo "    • mysql -u root -p -e \"CREATE DATABASE ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\""
  echo "    • mysql -u root -p < \"$SCRIPT_DIR/schema.sql\"   # full schema + user + sample data"
  echo ""
  return 1
}

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

echo "Checking MySQL database..."
bootstrap_mysql || true

echo "Applying migrations..."
python manage.py migrate --noinput

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
