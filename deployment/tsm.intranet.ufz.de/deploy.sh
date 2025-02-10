#!/usr/bin/env sh
cd "$(dirname "$0")/../.."
# todo: checkout origin main .env.example into temp.env
# run check using temp.env 
./compare_dotenv_files.py .env.example .env
git pull
rm remove-all-data.sh
sudo docker create --build
sudo docker compose up -d
sudo docker compose ps
