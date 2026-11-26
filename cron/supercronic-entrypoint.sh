#!/bin/bash

set -e

if [ "$SETUP_SERVICE" == "true" ]; then
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - starting cron-scheduler."
  # renders the crontab from the DSM DB and supervises supercronic
  exec python3 /scripts/cron_scheduler.py
else
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - skipping cron setup."
  echo "To start cron setup, set SETUP_SERVICE to 'true' in .env file."
fi
