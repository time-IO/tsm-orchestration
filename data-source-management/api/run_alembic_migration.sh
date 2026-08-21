#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/../../dc-with-dev.sh" run --rm --entrypoint "alembic upgrade head" dsm-api
