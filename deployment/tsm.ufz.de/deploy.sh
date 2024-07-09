#!/bin/bash
cd "$(dirname "$0")/../.."

export RELEASE_ENV_FILE="releases/${SSH_ORIGINAL_COMMAND}.env"

if [ ! -f "$RELEASE_ENV_FILE" ]; then
    echo "Release environment file not found: ${RELEASE_ENV_FILE}"
    exit 1
fi

git pull

DC="sudo docker compose --env-file .env --env-file ${RELEASE_ENV_FILE}"

# Deploy time.IO with the tag env file
$DC pull --quiet
$DC build --quiet
$DC up -d --force-recreate
sleep 10
$DC ps