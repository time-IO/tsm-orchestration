#!/usr/bin/env sh
cd "$(dirname "$0")/../.."

git pull
rm remove-all-data.sh
sudo docker compose build -q
sudo docker compose pull -q
sudo docker compose up -d
sudo docker compose ps
