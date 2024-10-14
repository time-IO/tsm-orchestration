#!/bin/bash
cd "$(dirname "$0")/../.."

# save current HEAD as fallback when release file does not exist
PREV_COMMIT=$(git rev-parse HEAD)

# fetch new commits but don't checkout on main
git fetch
# check out git TAG
git checkout ${SSH_ORIGINAL_COMMAND}

RELEASE_ENV_FILE="releases/${SSH_ORIGINAL_COMMAND}.env"

if [ ! -f "$RELEASE_ENV_FILE" ]; then
    echo "Release environment file not found: ${RELEASE_ENV_FILE}"
    # return HEAD back to PREV_COMMIT
    git checkout $PREV_COMMIT
    exit 1
fi

DC="sudo docker compose --env-file .env --env-file ${RELEASE_ENV_FILE}"

# Deploy time.IO with the tag env file
$DC pull --quiet
$DC build --quiet
$DC up -d --force-recreate
sleep 10
$DC ps