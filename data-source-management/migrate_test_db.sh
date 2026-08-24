#!/bin/bash
# Applies all pending Alembic migrations to the test database.
# Requires api-db-test to be running first:
#   ./dc-with-dev.sh up -d dsm-api-test-db
# Usage:
#   ./data-source-management/migrate_test_db.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DC="${SCRIPT_DIR}/../dc-with-dev.sh"

"${DC}" --profile test run --rm \
    -e POSTGRES_SERVER=dsm-api-test-db \
    -e POSTGRES_PORT=5432 \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=db_test \
    --entrypoint /bin/sh \
    dsm-api \
    -c 'alembic -c /app/alembic.ini upgrade head'