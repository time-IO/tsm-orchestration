#!/usr/bin/env bash
DIR_SCRIPT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker compose --env-file ../../.env -f "${DIR_SCRIPT}/docker-compose.yml" run --rm  all-things-publisher publish_all_things.py
