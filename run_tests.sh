#!/usr/bin/env bash

if [ $HOSTNAME != 'tsm' ]; then
  echo "This only works on stage/prod VM" >&2
  exit 2
fi
cd /home/tsm-orchestration/tsm-orchestration
source ../tests_venv/bin/activate
PGSSLROOTCERT=/etc/ssl/certs/ca-certificates.crt pytest --dc-env-file=.env tests -v
