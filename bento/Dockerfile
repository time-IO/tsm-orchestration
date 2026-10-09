# Base image: exact version tag, never a floating one (latest, major-only,
# trixie-slim, ...). Bump it deliberately in a merge request.
FROM ghcr.io/warpstreamlabs/bento:1.22.0

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Bento Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

# Ship the main configuration, static streams and entrypoint with the release
# they belong to, so deployments without a checkout of this repository (e.g.
# the Helm chart) run exactly the same configuration. Compose mounts the
# working tree over these paths to keep them editable without rebuilding the
# image. The repository files are world-readable, so COPY keeps them readable
# for the arbitrary non-root UID the container runs as.
# Dynamic streams are persisted to and restored from /data, which needs a
# writable volume.
COPY main.yaml /bento.yaml
COPY streams /streams
COPY --chmod=755 entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
