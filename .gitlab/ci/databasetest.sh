#!/bin/ash
exists="$(psql 'postgresql://postgres:postgres@127.0.0.1:5432' -tAc
      \"SELECT 1 FROM pg_roles WHERE
      rolname='myfirstproject_6185a5b8462711ec910a125e5a40a845'\
)"
if [ "$running" != 0 ]; then
  exit 1
else
  echo "Database is working correctly"
fi
