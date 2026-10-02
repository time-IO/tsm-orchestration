ARG BASE_IMAGE_REGISTRY=flyway/flyway
ARG BASE_IMAGE_TAG=latest

FROM ${BASE_IMAGE_REGISTRY}:${BASE_IMAGE_TAG}

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Flyway Migrations Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

# Ship the public schema migrations with the release they belong to, so
# deployments without a checkout of this repository (e.g. the Helm chart)
# run exactly the same set. Compose mounts the working tree over these paths.
COPY migrations/public /flyway/sql
COPY flyway-public.conf /flyway/conf/flyway.conf
