# Exact version tag, never a floating one.
FROM ghcr.io/lhns/mosquitto-go-auth:3.5.0-mosquitto_2.1.2

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO MQTT Broker Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

COPY mosquitto.conf /etc/mosquitto/config/mosquitto.conf
COPY mosquitto.tls.conf /etc/mosquitto/config/tls/mosquitto.tls.conf
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh

# Base image is rarely rebuilt, so pull in Debian security fixes ourselves.
RUN apt-get update \
    && apt-get -y upgrade \
    && rm -rf /var/lib/apt/lists/*

# Writable for any non-root UID, also without tmpfs/volume.
RUN chmod 1777 /var/lib/mosquitto \
    && mkdir -p /tmp/mosquitto \
    && chmod 1777 /tmp/mosquitto

ENTRYPOINT ["/usr/bin/tini", "--", "/docker-entrypoint.sh"]
CMD ["/usr/sbin/mosquitto", "-c", "/var/lib/mosquitto/mosquitto.conf"]
