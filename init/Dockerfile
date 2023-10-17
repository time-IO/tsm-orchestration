FROM alpine
ARG UID=1000

RUN apk add  --no-cache \
    openssh-keygen \
    openssl \
    tree
RUN adduser -u ${UID} -D tsm
COPY init.sh /init.sh
RUN chown tsm /init.sh
CMD ["/init.sh"]