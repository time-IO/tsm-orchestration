#!/bin/bash

set -e

start_supercronic() {
  echo "Starting supercronic with: /tmp/cron/crontab.txt"
  # Start supercronic with crontab file
  supercronic -split-logs /tmp/cron/crontab.txt  &
  SUPERCRONIC_PID=$!
}

stop_supercronic() {
  if [ $SUPERCRONIC_PID -ne 0 ]; then
    echo "Stopping supercronic with PID: $SUPERCRONIC_PID"
    kill -s SIGTERM $SUPERCRONIC_PID
    wait $SUPERCRONIC_PID
  fi
}

if [ "$SETUP_SERVICE" == "true" ]; then
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - starting cron setup."
  # Monitor crontab.txt for changes and update crontab if they occur
  # run loop in background to start cron service
  while true; do
    start_supercronic
    inotifywait -e modify /tmp/cron/crontab.txt
    echo "Crontab file is modified, restarting supercronic."
    stop_supercronic || echo "Failed to stop supercronic."
  done
else
  echo "SETUP_SERVICE has value '$SETUP_SERVICE' - skipping cron setup."
  echo "To start cron setup, set SETUP_SERVICE to 'true' in .env file."
fi
