#!/usr/bin/env sh
cd "$(dirname "$0")/../.."

# temp.env is a temporary file that contains the .env.example from the main branch
TEMP_ENV_FILE=$(mktemp)
git fetch origin main
git show origin/main:.env.example > $TEMP_ENV_FILE

# compare the .env file with the .env.example file from the main branch
# if it fails, remove TEMP_ENV_FILE and exit
# if it passes, remove TEMP_ENV_FILE and continue
./compare_dotenv_files.py .env $TEMP_ENV_FILE
if [ $? -ne 0 ]; then
  rm $TEMP_ENV_FILE
  exit 1
fi
rm $TEMP_ENV_FILE

git checkout main
git pull origin main
rm remove-all-data.sh
sudo docker compose pull -q
sudo docker compose up -d
sudo docker compose ps
