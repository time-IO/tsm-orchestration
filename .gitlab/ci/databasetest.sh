#!/bin/bash
exists="$(psql 'postgresql://postgres:postgres@docker:5432' -tAc "SELECT 1 FROM pg_roles WHERE rolname='yfirstproject_6185a5b8462711ec910a125e5a40a845'")"
if [ "$exists" != 1 ]; then
  exit 1
else
  echo "Database is working correctly"
fi
