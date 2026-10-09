#!/bin/bash
set -e


# Set permissions
user="$(id -u)"
if [ "$user" = '0' ]; then
  [ -d "/mosquitto" ] && chown -R mosquitto:mosquitto /mosquitto || true
fi

# the persistence volume is prepared by init/init.sh in Compose; create the
# directories here as well, so the image also starts without it
mkdir -p /tmp/mosquitto/auth /tmp/mosquitto/data

# create password db when not present
if [ ! -f "/tmp/mosquitto/auth/mosquitto.passwd" ]; then
  echo `echo -n "$MQTT_USER:" && /mosquitto/pw -p "$MQTT_PASSWORD"` >> /tmp/mosquitto/auth/mosquitto.passwd &&
  echo `echo -n "$MQTT_INGEST_USER:" && /mosquitto/pw -p "$MQTT_INGEST_PASSWORD"` >> /tmp/mosquitto/auth/mosquitto.passwd
fi

# always update acl file
{
  echo "user $MQTT_USER"
  echo "topic readwrite #"
  echo "topic read \$SYS/#"
  echo ""
  echo "# Each user has its own topic and logging namespace"
  echo "pattern readwrite mqtt_ingest/%u/#"
  echo "pattern readwrite logging/%u/#"
  echo ""
  echo "user $MQTT_INGEST_USER"
  echo "topic read mqtt_ingest/#"
  echo "topic readwrite health/#"
} >/tmp/mosquitto/auth/mosquitto.acl

mkdir -p /var/lib/mosquitto/tls

# substitute env vars in config template
( echo "cat <<EOF" ; cat /etc/mosquitto/config/mosquitto.conf ; echo EOF ) | sh > /var/lib/mosquitto/mosquitto.conf

# the TLS listener expects its certificates in /tmp/mosquitto/certs
if [ "${MQTT_TLS_ENABLED:-false}" = "true" ]; then
  ( echo "cat <<EOF" ; cat /etc/mosquitto/config/tls/mosquitto.tls.conf ; echo EOF ) | sh > /var/lib/mosquitto/tls/mosquitto.tls.conf
else
  rm -f /var/lib/mosquitto/tls/mosquitto.tls.conf
fi
echo "$@"
exec "$@"
