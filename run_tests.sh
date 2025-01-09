#!/usr/bin/env bash

if [ $HOSTNAME != 'tsm' ]; then
  echo "This only works on stage/prod VM" >&2
  exit 2
fi
pushd /home/tsm-orchestration/tsm-orchestration >/dev/null || exit 1
source ../venv_testing/bin/activate
PGSSLROOTCERT=/etc/ssl/certs/ca-certificates.crt pytest --dc-env-file=.env tests -v
EXIT_CODE=$?
deactivate
popd >/dev/null || exit 1
exit $EXIT_CODE
