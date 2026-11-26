#!/bin/bash

# healthy: supercronic runs and cron_scheduler.py touched its heartbeat within 3 polls
poll="${CRON_SCHEDULER_POLL_INTERVAL_SECONDS:-60}"
heartbeat="${CRON_DIR:-/tmp/crontab}/.heartbeat"

running=false
for cmd in /proc/[0-9]*/cmdline; do
  tr '\0' ' ' < "$cmd" 2>/dev/null | grep -q "^supercronic -split-logs" && running=true && break
done
if [ "$running" != true ]; then
  echo "Supercronic is not running."
  exit 1
fi

import_failed="${CRON_DIR:-/tmp/crontab}/.import-failed"
if [ -f "$import_failed" ]; then
  head -c 1000 "$import_failed"
  exit 1
fi

if [ ! -f "$heartbeat" ]; then
  echo "No heartbeat at $heartbeat."
  exit 1
fi
age=$(( $(date +%s) - $(stat -c %Y "$heartbeat") ))
if [ "$age" -gt $(( 3 * poll )) ]; then
  echo "Heartbeat is ${age}s old."
  exit 1
fi
echo "Supercronic is running, heartbeat ${age}s old."
