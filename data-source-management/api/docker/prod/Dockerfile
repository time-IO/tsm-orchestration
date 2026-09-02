ARG BASE_IMAGE_REGISTRY=python
ARG BASE_IMAGE_TAG=3.13-slim

# See https://hub.docker.com/_/python/
FROM ${BASE_IMAGE_REGISTRY}:${BASE_IMAGE_TAG} AS base

# Install Tkinter runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk \
    && rm -rf /var/lib/apt/lists/*

FROM base AS build

COPY ./data-source-management/api/requirements.txt /tmp/requirements.txt

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

FROM base AS dist

# Copy the virtual environment from the build stage
COPY --from=build /opt/venv /opt/venv

# Search in the virtual environment first
ENV PATH="/opt/venv/bin:$PATH"

# Create application directory and non-root user
ARG UID=1000
RUN mkdir /app && \
    adduser --uid ${UID} --disabled-password appuser

# Copy application as appuser
COPY --chown=${UID}:${UID} ./data-source-management/api/app /app
RUN chmod 755 /app/start.sh

# Copy external timeio library
COPY --chown=${UID}:${UID} ./src/timeio /app/timeio

WORKDIR /app
USER appuser

ENTRYPOINT ["/app/start.sh"]