#!/usr/bin/env sh
cd "$(dirname "$0")/../.."

git pull
sudo docker-compose pull
sudo docker-compose up -d
sudo docker-compose ps
