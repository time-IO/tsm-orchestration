#!/usr/bin/env sh
cd "$(dirname "$0")/../.."

git pull
sudo docker-compose pull -q
sudo docker-compose up --quiet-pull -d
sudo docker-compose ps
