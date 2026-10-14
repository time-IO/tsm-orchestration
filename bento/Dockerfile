# Base image: exact version tag, never a floating one (latest, major-only,
# trixie-slim, ...). Bump it deliberately in a merge request
FROM ghcr.io/warpstreamlabs/bento:1.22.0

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Bento Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

# Dynamic streams persist in /data, which needs a writable volume.
COPY main.yaml /bento.yaml
COPY streams /streams
COPY --chmod=755 entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
