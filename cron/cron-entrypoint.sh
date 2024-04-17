#!/bin/bash

set -e

# Function to update crontab from crontab.txt
update_crontab() {
  # prepend environment variables to /tmp/new_crontab.txt 
  # to be able topass them to cron jobs
  (printenv; cat /tmp/crontab.txt) > /tmp/new_crontab.txt
  # use /tmp/new_crontab.txt as crontab
  crontab /tmp/new_crontab.txt
}

if [ "$SETUP_SERVICE" == "true" ]; then
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - starting cron setup."
  # Monitor crontab.txt for changes and update crontab if they occurr 
  # run loop in background to start cron service
  while true; do
    update_crontab
    inotifywait -e modify /tmp/crontab.txt  
  done &
  sleep 1
  cron -f || exit 1
else
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - skipping cron setup."
  echo "To start cron setup, set SETUP_SERVICE to 'true' in .env file."
fi
