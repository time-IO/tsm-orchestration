#!/bin/bash

if [ -z "$1" ]; then
  echo "Error: migration name is required"
  echo "Usage: $(basename "$0") <migration-name>"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "${SCRIPT_DIR}/../docker-compose.yml" run --entrypoint "alembic revision --autogenerate -m '$1'" api
