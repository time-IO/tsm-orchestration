#!/bin/bash
# Runs integration tests inside the api container to ensure a consistent
# environment regardless of local library versions (e.g. libpq).
# Script automatically starts and stops required services.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DC="${SCRIPT_DIR}/../dc-with-dev.sh"

cleanup() {
    echo "Stopping test database..."
    "${DC}" --profile test stop dsm-api-test-db >/dev/null 2>&1 || true

    echo "Removing test database container..."
    "${DC}" --profile test rm -f dsm-api-test-db >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "Starting test database..."
"${DC}" --profile test up -d --wait dsm-api-test-db

echo "Running database migrations..."
"${SCRIPT_DIR}/migrate_test_db.sh"

echo "Running integration tests..."
"${DC}" run --rm --no-deps \
    -e POSTGRES_TEST_SERVER=dsm-api-test-db \
    -e POSTGRES_TEST_PORT=5432 \
    -e POSTGRES_TEST_USER=postgres \
    -e POSTGRES_TEST_PASSWORD=postgres \
    -e POSTGRES_TEST_DB=db_test \
    --entrypoint /bin/sh \
    dsm-api \
    -c 'python -m pytest tests/integration_tests/ -v "$@"' \
    -- "$@"