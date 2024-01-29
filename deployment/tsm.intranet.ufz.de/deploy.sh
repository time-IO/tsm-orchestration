#!/usr/bin/env sh
cd "$(dirname "$0")/../.."

git pull
rm remove-all-data.sh
sudo docker compose pull -q
sudo docker compose -f docker-compose.yml -f docker-compose-base.yml -f docker-compose-worker.yml up --quiet-pull -d
sudo docker compose ps
