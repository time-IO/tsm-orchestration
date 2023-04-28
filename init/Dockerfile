FROM alpine
ARG UID=1000

RUN apk add  --no-cache \
    openssh-keygen \
    openssl
RUN adduser -u ${UID} -D tsm
COPY init.sh /init.sh
CMD ["/init.sh"]