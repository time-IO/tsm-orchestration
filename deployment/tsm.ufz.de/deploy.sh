#!/bin/bash
cd "$(dirname "$0")/../.."

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <argument>"
    exit 1
fi

export TAG=$1
export TAG_ENV="./releases/${TAG}.env"

if [ ! -f "$TAG_ENV" ]; then
    echo "Release environment file not found: $TAG_ENV"
    exit 1
fi

git pull

DC="docker compose --env-file .env --env-file ${TAG_ENV}"
$DC pull --quiet
$DC build --quiet
$DC up -d --force-recreate
sleep 10
$DC ps