#!/bin/bash

MAX_ATTEMPTS="${RESTART_MAX_ATTEMPTS:-3}"
WINDOW_SECONDS="${RESTART_WINDOW_SECONDS:-10}"

if [[ $# -gt 0 ]]; then
  CMD="$@"
elif [[ -n "${CMD}" ]]; then
  CMD="${CMD}"
else
  echo "Error: No command provided."
  exit 1
fi

attempts=0
start_time=$(date +%s)

while true; do
  echo "Attempt $((attempts + 1)) of ${MAX_ATTEMPTS} to start container with command: $CMD"
  $CMD && exit 0

  # Increment attempts and check time window
  attempts=$((attempts + 1))
  now=$(date +%s)
  elapsed=$((now - start_time))


  # only count as failed attempt if within the window
  if [[ $elapsed -le $WINDOW_SECONDS ]]; then
    if [[ $attempts -eq $MAX_ATTEMPTS ]]; then
      echo "Error: Command failed after $attempts attempts within the first $WINDOW_SECONDS seconds."
      # We exit with a non-zero status to not restart the container.
      exit 0
    fi
  else
    # reset attempts and timer if outside the window
    echo "Failed attempt outside of $WINDOW_SECONDS seconds window. Resetting attempt counter."
    attempts=0
    start_time=$now
  fi
done

echo "MAX_ATTEMPTS: $MAX_ATTEMPTS"
echo "WINDOW_SECONDS: $WINDOW_SECONDS"
echo "CMD: $CMD"