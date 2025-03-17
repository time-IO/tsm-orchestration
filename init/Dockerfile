ARG BASE_IMAGE_TAG=latest

FROM alpine:${BASE_IMAGE_TAG}
ARG UID=1000

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Init Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.version="0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

RUN apk add  --no-cache \
    openssh-keygen \
    openssl \
    tree
RUN adduser -u ${UID} -D tsm
COPY init.sh /init.sh
RUN chown tsm /init.sh
USER tsm
RUN mkdir /home/tsm/html
RUN mkdir -p /tmp/minio \
    && mkdir -p /tmp/cron
CMD ["/init.sh"]