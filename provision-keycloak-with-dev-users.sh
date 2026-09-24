#!/usr/bin/env bash

set -euo pipefail

KEYCLOAK_CONTAINER="keycloak"
REALM="timeio"

echo "Delete realm '$REALM'..."

./dc-with-dev.sh exec -T "$KEYCLOAK_CONTAINER" \
  /opt/keycloak/bin/kcadm.sh delete "realms/$REALM" \
  --server http://proxy/keycloak \
  --realm master \
  --user keycloak \
  --password keycloak

echo "Realm deleted."

echo "Restarting Keycloak..."
./dc-with-dev.sh restart "$KEYCLOAK_CONTAINER"

echo "Keycloak restarted. Realm will be re-imported."
