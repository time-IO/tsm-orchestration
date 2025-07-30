#!/bin/sh

echo "[MQTT CHECK] Starting MQTT connectivity check..."

MAX_ATTEMPTS=${MQTT_MAX_ATTEMPTS:-60}
SLEEP_SECONDS=${MQTT_SLEEP_SECONDS:-5}
COUNT=0
MQTT_TEST_TOPIC=${MQTT_TEST_TOPIC:-"test"}

echo $(env | grep MQTT)

echo "MQTT_BROKER: ${MQTT_BROKER:-'mqtt-broker:1883'}"
MQTT_HOST=$(echo "$MQTT_BROKER" | cut -d':' -f1)
echo "MQTT_HOST: ${MQTT_HOST}"
MQTT_PORT=$(echo "$MQTT_BROKER" | cut -d':' -f2)
echo "MQTT_PORT: ${MQTT_PORT}"
echo "MQTT_TEST_TOPIC: ${MQTT_TEST_TOPIC:-test}"
echo "MQTT_USER: ${MQTT_USER:-not set}"
echo "MQTT_PASSWORD: ${MQTT_PASSWORD:-not set}"

while [ $COUNT -lt $MAX_ATTEMPTS ]; do
  echo "[MQTT CHECK] Attempt $(($COUNT + 1)) of $MAX_ATTEMPTS..."

  timeout 1 mosquitto_sub -h "$MQTT_HOST" -p "$MQTT_PORT" -t "$MQTT_TEST_TOPIC" -C 1 -q 0\
    -u "$MQTT_USER" -P "$MQTT_PASSWORD"

  if [ $? -eq 0 ]; then
    echo "[MQTT CHECK] Successfully connected to MQTT broker."
    exit 0
  fi

  echo "[MQTT CHECK] Failed to connect. Retrying in ${SLEEP_SECONDS}s..."
  COUNT=$(($COUNT + 1))
  sleep $SLEEP_SECONDS
done

echo "[MQTT CHECK] Failed to connect to MQTT broker after $MAX_ATTEMPTS attempts."
exit 1
