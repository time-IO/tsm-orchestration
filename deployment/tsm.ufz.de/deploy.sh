#!/bin/bash
cd "$(dirname "$0")/../.."

TEMP_ENV_FILE=$(mktemp)
git fetch origin
git show origin/main:.env.example > $TEMP_ENV_FILE

# compare the .env file with the .env.example file from the main branch
# if it fails, rm TEMP_ENV_FILE and exit
# if it passes, rm TEMP_ENV_FILE and continue
./compare_dotenv_files.py .env $TEMP_ENV_FILE
if [ $? -ne 0 ]; then
  rm $TEMP_ENV_FILE
  exit 1
fi
rm $TEMP_ENV_FILE

git checkout ${SSH_ORIGINAL_COMMAND}

# check whether the tag and the release environment file exist
# fail if it does not exist ...
RELEASE_ENV_FILE="releases/${SSH_ORIGINAL_COMMAND}.env"
git show ${SSH_ORIGINAL_COMMAND}:${RELEASE_ENV_FILE} || exit 1

# ... otherwise deploy time.IO with the tag env file
DC="sudo docker compose --env-file .env --env-file ${RELEASE_ENV_FILE}"
$DC create --build
$DC up -d
sleep 10
$DC ps
