# Base image: exact version tag, never a floating one (latest, major-only,
# trixie-slim, ...). Bump it deliberately in a merge request.
FROM grafana/grafana:11.6.16

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Visualization Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

COPY provisioning /etc/grafana/provisioning
