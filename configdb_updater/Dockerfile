ARG BASE_IMAGE_REGISTRY=python
ARG BASE_IMAGE_TAG=3.11-slim

FROM ${BASE_IMAGE_REGISTRY}:${BASE_IMAGE_TAG}

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO ConfigDB Updater Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.version="0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

# Dockerfile template from:
# https://hub.docker.com/_/python/

WORKDIR /usr/src/app

COPY src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

# create a non-root user
ARG UID=1000
RUN adduser --uid ${UID} --disabled-password appuser
RUN chown -R appuser:appuser /usr/src/app
USER appuser

# enable sslmode verify-full
ENV PGSSLROOTCERT=/etc/ssl/certs/ca-certificates.crt

ENTRYPOINT ["python3"]


# RUN apk update && apk add bash gcc musl-dev libpq-dev

