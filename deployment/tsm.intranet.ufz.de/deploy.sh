#!/usr/bin/env sh
cd "$(dirname "$0")/../.."

git pull
rm remove-all-data.sh
sudo docker create --build
sudo docker compose up -d
sudo docker compose ps
