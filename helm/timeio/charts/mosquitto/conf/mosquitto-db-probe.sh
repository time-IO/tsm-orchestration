# !/bin/sh

# This script is used to probe the Mosquitto Authentication database

# It checks if the database is accessible and returns the status

RETRIES=30
SLEEP=3

echo "Checking PostgresDB for Connectivity and MQTT Authentication"

echo "postgesql://${MQTT_AUTH_POSTGRES_USER}:${MQTT_AUTH_POSTGRES_PASS}@${MQTT_AUTH_POSTGRES_HOST}:${MQTT_AUTH_POSTGRES_PORT}/${MQTT_AUTH_POSTGRES_DB}"

for i in $(seq 1 $RETRIES); do
    PGPASSWORD=${MQTT_AUTH_POSTGRES_PASS} \
    psql -h ${MQTT_AUTH_POSTGRES_HOST} \
         -p ${MQTT_AUTH_POSTGRES_PORT} \
         -U ${MQTT_AUTH_POSTGRES_USER} \
         -d ${MQTT_AUTH_POSTGRES_DB} \
         -c "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Mosquitto Authentication database is accessible"
        exit 0
    fi
    echo "Mosquitto Authentication database is not accessible, retrying in $SLEEP seconds..."
    sleep $SLEEP
done

exit 1