#!/bin/bash
# Applies all pending Alembic migrations to the test database.
# Requires api-db-test to be running first:
#   docker compose up -d --wait api-db-test
# Usage:
#   ./api/migrate_test_db.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker compose -f "${SCRIPT_DIR}/../docker-compose.yml" run --rm \
  -e POSTGRES_SERVER=api-db-test \
    -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=db_test \
  --entrypoint "alembic upgrade head" \
  api