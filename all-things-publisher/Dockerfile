ARG BASE_IMAGE_TAG=3.11-slim
ARG UID=1000

FROM python:${BASE_IMAGE_TAG}

WORKDIR /usr/src/app

COPY all-things-publisher/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/timeio/common.py ./timeio/common.py
COPY src/timeio/databases.py ./timeio/databases.py
COPY src/timeio/mqtt.py ./timeio/mqtt.py
COPY src/timeio/errors.py ./timeio/errors.py
COPY src/publish_all_things.py .

# create a non-root user
ARG UID=1000
RUN adduser --uid ${UID} --disabled-password appuser
RUN chown -R appuser:appuser /usr/src/app
USER appuser
