#!/bin/sh
set -eu

mkdir -p /app/pdf_temp
mkdir -p /app/.cache/fontconfig
chown -R appuser:appuser /app/pdf_temp /app/.cache

export HOME=/app
export XDG_CACHE_HOME=/app/.cache

exec celery -A celery_app.celery worker \
  --loglevel=info \
  --concurrency=2 \
  --uid=appuser \
  --gid=appuser
