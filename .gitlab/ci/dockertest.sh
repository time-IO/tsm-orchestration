#!/bin/bash
running="$(docker compose ps --services --filter status=running | sort)"
services="$(docker compose config --services | grep -v -e init -e flyway | sort)"
if [ "$running" != "$services" ]; then
    echo "Following services are not running:"
    # Bash specific
    comm -13 <(sort <<<"$running") <(sort <<<"$services")
    exit 1
else
    echo "All services are running"
    exit 0
fi
