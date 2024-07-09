#!/usr/bin/env sh
cd "$(dirname "$0")/../.."

git pull
rm remove-all-data.sh
sudo docker compose pull -q
sudo docker compose build -q
sudo docker compose up --quiet-pull -d
sudo docker compose ps
