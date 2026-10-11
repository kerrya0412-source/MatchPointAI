#!/bin/bash
set -e

echo "MatchPoint AI startup"
echo "Working directory: $(pwd)"
echo "APP_PATH: ${APP_PATH:-not set}"

APP_DIR="${APP_PATH:-$(pwd)}"

echo "Application directory: $APP_DIR"
echo "Directory contents:"
ls -la "$APP_DIR"

exec python -m uvicorn backend.app.main:app \
    --app-dir "$APP_DIR" \
    --host 0.0.0.0 \
    --forwarded-allow-ips "127.0.0.1,::1,169.254.129.1" \
    --port "${PORT:-8000}"

