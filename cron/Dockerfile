ARG BASE_IMAGE_TAG=bullseye-slim

FROM debian:${BASE_IMAGE_TAG}

ARG BUILD_DATE
ARG VCS_REF
ARG SUPERCRONIC_VERSION=0.2.33

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Cron-Scheduler Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.version="0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl tini python3 python3-pip inotify-tools \
    && rm -rf /var/lib/apt/\
    && rm -rf /etc/cron.*/*

COPY src/constraints.txt .
COPY src/requirements.cron-scheduler.txt ./requirements.txt
COPY cron/supercronic-entrypoint.sh .
COPY cron/supercronic-health.sh .

RUN curl -fsSLO https://github.com/aptible/supercronic/releases/download/v${SUPERCRONIC_VERSION}/supercronic-linux-amd64 \
    && chmod 755 supercronic-linux-amd64 \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic \
    && chmod 755 /supercronic-entrypoint.sh \
    && chmod 755 /supercronic-health.sh

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -c constraints.txt

ARG UID=1000
ARG USER=tsm

RUN useradd --uid ${UID} -m -d /home/${USER} -s /bin/bash ${USER}

ENV PGSSLROOTCERT=/etc/ssl/certs/ca-certificates.crt
ENV STDOUT=/proc/1/fd/1
ENV STDERR=/proc/1/fd/2
ENV PYTHONPATH=/scripts/timeio

USER ${UID}

ENTRYPOINT ["tini", "--"]
CMD ["sh", "-c", "/supercronic-entrypoint.sh"]
