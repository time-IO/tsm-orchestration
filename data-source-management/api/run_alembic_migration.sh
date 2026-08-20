#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "${SCRIPT_DIR}/../../docker-compose.yml" -f "${SCRIPT_DIR}/../../docker-compose-dev.yml" run --rm --entrypoint "alembic upgrade head" dsm-api