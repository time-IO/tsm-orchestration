#!/bin/bash
set -e


# Set permissions
user="$(id -u)"
if [ "$user" = '0' ]; then
  [ -d "/mosquitto" ] && chown -R mosquitto:mosquitto /mosquitto || true
fi

# create password db when not present
if [ ! -f "/mosquitto-auth/mosquitto.passwd" ]; then
  echo `echo -n "$MQTT_USER:" && /mosquitto/pw -p "$MQTT_PASSWORD"` >> /mosquitto-auth/mosquitto.passwd &&
  echo `echo -n "$MQTT_INGEST_USER:" && /mosquitto/pw -p "$MQTT_INGEST_PASSWORD"` >> /mosquitto-auth/mosquitto.passwd
  echo `echo -n "$FRONTEND_MQTT_USER:" && /mosquitto/pw -p "$FRONTEND_MQTT_PASS"` >> /mosquitto-auth/mosquitto.passwd
fi

# create acl file when not present
if [ ! -f /mosquitto-auth/mosquitto.acl ]; then
  {
    echo "user $MQTT_USER"
    echo "topic readwrite #"
    echo "topic read \$SYS/#"
    echo "topic readwrite thing_creation"
    echo "topic readwrite logging/#"
    echo "topic readwrite object_storage_notification"
    echo ""
    echo "# Each user has its own topic and logging namespace"
    echo "pattern readwrite mqtt_ingest/%u/#"
    echo "pattern readwrite logging/%u/#"
    echo ""
    echo "user $MQTT_INGEST_USER"
    echo "topic read mqtt_ingest/#"
    echo ""
    echo "user $FRONTEND_MQTT_USER"
    echo "topic readwrite thing_creation/#"
    echo "topic readwrite user_login/#"
  } >>/mosquitto-auth/mosquitto.acl
fi

if [ ! -d "/var/lib/mosquitto/tls" ]
then
    mkdir ./var/lib/mosquitto/tls
fi

# substitute env vars in config template
( echo "cat <<EOF" ; cat /etc/mosquitto/config/mosquitto.conf ; echo EOF ) | sh > /var/lib/mosquitto/mosquitto.conf
( echo "cat <<EOF" ; cat /etc/mosquitto/config/tls/mosquitto.tls.conf ; echo EOF ) | sh > /var/lib/mosquitto/tls/mosquitto.tls.conf
echo "$@"
exec "$@"
