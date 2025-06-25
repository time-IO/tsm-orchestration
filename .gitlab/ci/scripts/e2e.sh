#!/bin/bash

# run local with localhost
HOST=docker
# run local with /tmp
BIN_DIR=$HOME

echo "installing fixtures.."
docker compose exec -T frontend python3 manage.py loaddata user.json
sleep 1
docker compose exec -T frontend python3 manage.py loaddata thing.json
sleep 1
docker compose exec -T frontend python3 manage.py dumpdata tsm.thing > thing_dump.json
docker compose exec -T frontend python3 manage.py dumpdata tsm.database > database.json
docker compose exec -T frontend python3 manage.py dumpdata tsm.rawdatastorage > object-storage.json

echo
echo "testing visualization end-to-end..."
THING_UID=$(cat thing_dump.json | jq -r .[].fields.thing_id)
echo THING_UID: $THING_UID
GROUP_ID=$(cat thing_dump.json | jq -r .[].fields.group)
echo GROUP_ID: $GROUP_ID
GROUP_UID=$(python3 -c "import uuid; print(uuid.UUID(int=${GROUP_ID}))")
echo GROUP_UID: $GROUP_UID
GF_API=http://$HOST/visualization/api

curl -IsS -u grafana:grafana ${GF_API}/dashboards/uid/${THING_UID} || exit 1
curl -IsS -u grafana:grafana ${GF_API}/dashboards/uid/${GROUP_UID} || exit 1
curl -IsS -u grafana:grafana ${GF_API}/datasources/uid/${GROUP_UID} || exit 1
curl -sf -u grafana:grafana ${GF_API}/teams/search?uid=${GROUP_UID} > teams.json || exit 1
TEAMS_ID=$(cat teams.json | jq -r .teams[0].orgId)
TEAMS_UID=$(python3 -c "import uuid; print(uuid.UUID(int=${TEAMS_ID}))")
echo $TEAMS_UID
[ \"$TEAMS_UID\" == \"$GROUP_UID\" ] || exit 1
echo
echo 'testing object storage end-to-end...'
MINIO_USER=$(cat object-storage.json | jq -r '.[].fields.access_key')
MINIO_PASSWORD=$(cat object-storage.json | jq -r '.[].fields.secret_key')
curl https://dl.min.io/client/mc/release/linux-amd64/mc --create-dirs -o $BIN_DIR/minio-binaries/mc
chmod +x $BIN_DIR/minio-binaries/mc
export PATH=$PATH:$BIN_DIR/minio-binaries/
mc alias set minio http://$HOST:9000 minioadmin minioadmin
mc ls --summarize minio || exit 1
sleep 1
curl -u ${MINIO_USER}:${MINIO_PASSWORD} ftp://$HOST:40021 -I -s -o /dev/null && echo OK || exit 1
echo
echo 'testing database end-to-end...'
DB_USER=$(cat database.json | jq -r '.[].fields.username')
DB_PASSWORD=$(cat database.json | jq -r '.[].fields.password')
DB_NAME=$(cat database.json | jq -r '.[].fields.name')
PGPASSWORD=${DB_PASSWORD} psql -U ${DB_USER} -h $HOST -d ${DB_NAME} -tAc "SELECT * from ${DB_USER}.thing" && echo OK || exit 1
echo
echo 'testing frost end-to-end...'
curl -IsS http://$HOST/sta/${DB_USER} -o /dev/null && echo OK || exit 1
