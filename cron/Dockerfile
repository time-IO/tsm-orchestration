FROM debian:bullseye-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron tini python3 python3-pip\
    && rm -rf /var/lib/apt/

RUN rm -rf /etc/cron.*/*

COPY requirements.txt .

# upgrade pip and ensure pip, then install requirements
RUN pip install --no-cache-dir -r requirements.txt

ARG UID=1000
ARG USER=tsm

RUN useradd --uid ${UID} -m -d /home/${USER} -s /bin/bash ${USER}

RUN chmod gu+rw /var/run \
    && chmod gu+s /usr/sbin/cron

USER ${UID}

COPY crontab.txt .

ENTRYPOINT ["tini", "--"]

CMD ["sh", "-c", "(printenv; cat /tmp/crontab.txt) > /tmp/new_crontab.txt && crontab /tmp/new_crontab.txt && cron -f"]
