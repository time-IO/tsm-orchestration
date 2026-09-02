#!/bin/bash

if [ -z "$1" ]; then
  echo "Error: migration name is required"
  echo "Usage: $(basename "$0") <migration-name>"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/../../dc-with-dev.sh" run --rm --entrypoint "alembic revision --autogenerate -m '$1'" dsm-api
