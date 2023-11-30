FROM debian:bullseye-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron tini python3 python3-pip\
    && rm -rf /var/lib/apt/\
    && rm -rf /etc/cron.*/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ARG UID=1000
ARG USER=tsm

RUN useradd --uid ${UID} -m -d /home/${USER} -s /bin/bash ${USER}

RUN chmod gu+rw /var/run \
    && chmod gu+s /usr/sbin/cron

USER ${UID}

ENV STDOUT=/proc/1/fd/1
ENV STDERR=/proc/1/fd/2

COPY cron-entrypoint.sh .

ENTRYPOINT ["tini", "--"]

CMD ["sh", "-c", "./cron-entrypoint.sh"]
