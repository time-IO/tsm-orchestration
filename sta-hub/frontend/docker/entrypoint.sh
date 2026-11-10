#!/bin/sh
set -e

if [ ! -d "/home/node/app/node_modules" ] || [ -z "$(ls -A /home/node/app/node_modules 2>/dev/null)" ]; then
    echo "node_modules not found - installing dependencies..."
    npm ci
else
    echo "node_modules already exists - skipping npm ci"
fi

exec "$@"