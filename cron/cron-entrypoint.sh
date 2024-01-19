#!/bin/bash

set -e

if [ "$SETUP_SERVICE" == "true" ]; then
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - starting cron setup."
  (printenv; cat /tmp/crontab.txt) > /tmp/new_crontab.txt
  crontab /tmp/new_crontab.txt
  cron -f || exit 1
  echo "cron setup complete."
else
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - skipping cron setup."
  echo "To start cron setup, set SETUP_SERVICE to 'true' in .env file."
fi