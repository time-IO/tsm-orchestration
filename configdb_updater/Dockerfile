FROM python:3.11

# Dockerfile template from:
# https://hub.docker.com/_/python/

WORKDIR /usr/src/app

COPY src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

# create a non-root user
ARG UID=1000
RUN adduser --uid ${UID} --disabled-password appuser
RUN chown -R appuser:appuser /usr/src/app
USER appuser

# enable sslmode verify-full
ENV PGSSLROOTCERT=/etc/ssl/certs/ca-certificates.crt

ENTRYPOINT ["python3"]


# RUN apk update && apk add bash gcc musl-dev libpq-dev

