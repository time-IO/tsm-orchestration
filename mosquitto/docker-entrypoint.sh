#!/bin/ash
set -e

# Set permissions
user="$(id -u)"
if [ "$user" = '0' ]; then
  [ -d "/mosquitto" ] && chown -R mosquitto:mosquitto /mosquitto || true
fi

# create password db when not present
if [ ! -f /mosquitto-auth/mosquitto.passwd ]; then
  mosquitto_passwd -c -b /mosquitto-auth/mosquitto.passwd "$MQTT_USER" "$MQTT_PASSWORD"
fi

# create acl file when not present
if [ ! -f /mosquitto-auth/mosquitto.acl ]; then
  {
    echo "user $MQTT_USER"
    echo "topic read #"
    echo "topic read \$SYS/#"
    echo "topic thing_creation"
    echo "topic logging/#"
    echo "topic object_storage_notification"
    echo ""
    echo "# Each user has its own topic namespace"
    echo "pattern readwrite %u/#"
  } >>/mosquitto-auth/mosquitto.acl
fi

exec "$@"
