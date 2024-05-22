FROM alpine
ARG UID=1000

RUN apk add  --no-cache \
    openssh-keygen \
    openssl \
    tree
RUN adduser -u ${UID} -D tsm
COPY init.sh /init.sh
RUN chown tsm /init.sh
USER tsm
RUN mkdir -p /tmp/minio/certs 
RUN mkdir -p /tmp/cron
RUN mkdir -p /tmp/mosquitto-auth
RUN mkdir -p /tmp/mosquitto-data
CMD ["/init.sh"]