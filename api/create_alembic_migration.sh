#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "${SCRIPT_DIR}/../docker-compose.yml" run --entrypoint "alembic revision --autogenerate -m '$1'" api
