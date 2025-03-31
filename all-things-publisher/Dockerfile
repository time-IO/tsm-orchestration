ARG BASE_IMAGE_TAG=3.11-slim
ARG UID=1000

FROM python:${BASE_IMAGE_TAG}

WORKDIR /usr/src/app

COPY src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

# create a non-root user
ARG UID=1000
RUN adduser --uid ${UID} --disabled-password appuser
RUN chown -R appuser:appuser /usr/src/app
USER appuser
