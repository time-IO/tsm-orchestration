#!/bin/bash
cd "$(dirname "$0")/../.."

export TAG=$SSH_ORIGINAL_COMMAND
export RELEASE_ENV_FILE="./releases/${TAG}.env"

if [ ! -f "$TAG_ENV" ]; then
    echo "Release environment file not found: ${RELEASE_ENV_FILE}"
    exit 1
fi

git pull

DC="docker compose --env-file .env --env-file ${RELEASE_ENV_FILE}"

# Deploy time.IO with the tag env file
$DC pull --quiet
$DC build --quiet
$DC up -d --force-recreate
sleep 10
$DC ps
