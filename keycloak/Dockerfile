ARG BASE_IMAGE_REGISTRY=quay.io/keycloak/keycloak
ARG BASE_IMAGE_TAG=latest

FROM ${BASE_IMAGE_REGISTRY}:${BASE_IMAGE_TAG}

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Keycloak Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

# Ship the realm import, login themes and providers with the release they
# belong to, so deployments without a checkout of this repository (e.g. the
# Helm chart) run exactly the same configuration. Compose mounts the working
# tree over these paths to keep them editable without rebuilding the image.
# The repository files are world-readable, so COPY keeps them readable for the
# arbitrary non-root UID the container runs as.
COPY keycloak-init.template.json /opt/keycloak/data/import/keycloak-init.json
COPY themes /opt/keycloak/themes
COPY plugins /opt/keycloak/providers
