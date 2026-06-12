#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting Django on PORT=${PORT:?PORT must be set by Railway} ==="

echo "=== migrate ==="
python manage.py migrate --noinput

echo "=== collectstatic ==="
python manage.py collectstatic --noinput

echo "=== gunicorn ==="
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --timeout 120 \
  --log-file - \
  --access-logfile -
