ARG BASE_IMAGE_TAG=bullseye-slim

FROM debian:${BASE_IMAGE_TAG} AS base

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Dispatcher Base Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.version="0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

RUN apt-get -y update \
    && apt-get -y dist-upgrade \
    && apt-get -y --no-install-recommends install \
      python3 \
      python3-tk \
      libaio1 \
      ca-certificates \
    && apt-get -y autoremove \
    && apt-get -y autoclean \
    && rm -rf /var/lib/apt

FROM base AS build

RUN apt-get -y update \
    && apt-get -y --no-install-recommends install \
      git openssh-client \
      python3-pip python3-venv \
      curl \
      unzip

# Install minio mc client
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc > /usr/local/bin/mc \
    && chmod a+x /usr/local/bin/mc

# add requirements
COPY src/constraints.txt /tmp/constraints.txt
COPY src/requirements.dispatcher.txt /tmp/requirements.txt
RUN python3 -m venv /venv \
    && . /venv/bin/activate \
    && pip install --upgrade pip \
    && pip install \
        --no-cache-dir \
        --no-warn-script-location \
        -r /tmp/requirements.txt -c /tmp/constraints.txt

FROM base AS dist

ARG UID=1000

# Create a group and user
RUN useradd --uid $UID -m appuser

COPY --from=build /venv /venv
COPY --from=build /usr/local/bin/mc /usr/local/bin/mc

# Tell docker that all future commands should run as the appuser user
USER appuser

ENV PGSSLROOTCERT=/etc/ssl/certs/ca-certificates.crt
ENV PATH="/venv/bin:$PATH"
WORKDIR /home/appuser/app/src

COPY --chown=appuser src .

ENTRYPOINT ["python3"]
