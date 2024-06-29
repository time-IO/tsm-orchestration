#!/bin/bash

set -e

CRONTAB_FILE="/tmp/crontab.txt"

# Function to filter and output environment variables
filter_env_vars() {
  printenv | while IFS='=' read -r name value; do
    # Check if the variable name is not empty, value is not empty, and value does not contain '='
    if [[ -n "$name" && -n "$value" && "$value" != *'='* ]]; then
      echo "${name}=${value}"
    fi
  done
}

# Function to create /tmp/crontab.txt if it doesn't exist
create_crontab_file() {
  if [ ! -f "$CRONTAB_FILE" ]; then
    touch "$CRONTAB_FILE"
    chmod 666 "$CRONTAB_FILE"
  fi
}

# Function to update crontab from crontab.txt
update_crontab() {
  # Prepend filtered environment variables to /tmp/new_crontab.txt
  # to be able to pass them to cron jobs
  (filter_env_vars; cat "$CRONTAB_FILE") > /tmp/new_crontab.txt
  # Use /tmp/new_crontab.txt as crontab
  crontab /tmp/new_crontab.txt
}

# Check and create /tmp/crontab.txt if it doesn't exist
create_crontab_file

if [ "$SETUP_SERVICE" == "true" ]; then
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - starting cron setup."
  # Monitor crontab.txt for changes and update crontab if they occur
  # Run loop in background to start cron service
  while true; do
    update_crontab
    inotifywait -e modify "$CRONTAB_FILE"
  done &
  sleep 1
  cron -f || exit 1
else
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - skipping cron setup."
  echo "To start cron setup, set SETUP_SERVICE to 'true' in .env file."
fi
