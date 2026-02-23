#!/bin/bash

# set dev settings as default
FASTAPI_ENV="${FASTAPI_ENV:-dev}"
FASTAPI_HOST="${FASTAPI_HOST:-0.0.0.0}"
FASTAPI_PORT="${FASTAPI_PORT:-8000}"

alembic upgrade head
fastapi $FASTAPI_ENV --host $FASTAPI_HOST --port $FASTAPI_PORT main.py
