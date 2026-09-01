#!/bin/bash
set -e

# set dev settings as default
FASTAPI_ENV="${FASTAPI_ENV:-dev}"
FASTAPI_HOST="${FASTAPI_HOST:-0.0.0.0}"
FASTAPI_PORT="${FASTAPI_PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"
## convert log level to lowercase
LOG_LEVEL="${LOG_LEVEL,,}"

alembic -c /app/alembic.ini upgrade head

if [ "$FASTAPI_ENV" = "dev" ]; then
	exec uvicorn main:app --host "$FASTAPI_HOST" --port "$FASTAPI_PORT" --reload --log-level "$LOG_LEVEL" --log-config /app/logging.json
else
	exec uvicorn main:app --host "$FASTAPI_HOST" --port "$FASTAPI_PORT" --log-level "$LOG_LEVEL" --log-config /app/logging.json
fi
