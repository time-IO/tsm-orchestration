#!/bin/bash
# Runs integration tests inside the api container to ensure a consistent
# environment regardless of local library versions (e.g. libpq).
# Requires: docker compose up -d


docker exec -it datasource-management-api-dev bash -c "
cd /app && \
POSTGRES_TEST_SERVER=api-db-test \
POSTGRES_TEST_PORT=5432 \
POSTGRES_TEST_USER=postgres \
POSTGRES_TEST_PASSWORD=postgres \
POSTGRES_TEST_DB=db_test \
python -m pytest tests/integration_tests/ -v \$@
"
