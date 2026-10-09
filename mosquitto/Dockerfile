# Base image: exact version, never a floating one (latest, major-only,
# trixie-slim, ...). Bump it deliberately in a merge request. The upstream
# project publishes mosquitto 2.1.2 only under a branch tag, so the digest
# pins the exact build.
FROM ghcr.io/lhns/mosquitto-go-auth:master-mosquitto_2.1.2@sha256:c7cd465584020bd9e13d272fb9f3e598a757e2e6b7cbdd821ab0334e7cd60c9e

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO MQTT Broker Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

# Ship the broker configuration and entrypoint with the release they belong
# to, so deployments without a checkout of this repository (e.g. the Helm
# chart) run exactly the same configuration. Compose mounts the working tree
# over these paths to keep them editable without rebuilding the image. The
# repository files are world-readable, so COPY keeps them readable for the
# arbitrary non-root UID the container runs as.
COPY mosquitto.conf /etc/mosquitto/config/mosquitto.conf
COPY mosquitto.tls.conf /etc/mosquitto/config/tls/mosquitto.tls.conf
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh

# The entrypoint renders the configuration templates into /var/lib/mosquitto
# and creates the auth and data directories in /tmp/mosquitto (the persistence
# volume), so both have to be writable for the arbitrary non-root UID. Shipping
# /tmp/mosquitto also keeps it writable when only the certificates are mounted
# below it.
RUN chmod 1777 /var/lib/mosquitto \
    && mkdir -p /tmp/mosquitto \
    && chmod 1777 /tmp/mosquitto

ENTRYPOINT ["/usr/bin/tini", "--", "/docker-entrypoint.sh"]
CMD ["/usr/sbin/mosquitto", "-c", "/var/lib/mosquitto/mosquitto.conf"]
