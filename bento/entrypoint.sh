#!/bin/sh
set -e

/bento streams --prefix-stream-endpoints=false /streams/*/*.yaml &
BENTO_PID=$!
trap 'kill -TERM "$BENTO_PID" 2>/dev/null' TERM INT

i=0
until wget -qO- http://localhost:4195/streams >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "bento API did not become ready in time, skipping stream restore"
    break
  fi
  sleep 0.5
done

if [ -d /data/streams ]; then
  find /data/streams -type f -name '*.json' | while read -r f; do
    id=$(basename "$f" .json)
    echo "restoring stream: $id"
    wget -qS -O- --header="Content-Type: application/json" --post-file="$f" \
      "http://localhost:4195/streams/$id" || echo "failed to restore stream: $id"
  done
fi

wait "$BENTO_PID"
