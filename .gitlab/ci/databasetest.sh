#!/bin/bash
exists="$(psql 'postgresql://postgres:postgres@localhost:5432' -tAc "SELECT 1 FROM pg_roles WHERE rolname='postgres'")"
if [ "$exists" != 1 ]; then
  exit 1
else
  echo "Database is working correctly"
fi
