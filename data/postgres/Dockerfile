# start from ubuntu based timescale image
ARG DATABASE_IMAGE_TAG=pg14
FROM timescale/timescaledb-ha:${DATABASE_IMAGE_TAG}

# switch from postgres/1000 to root and install postgis
USER root
RUN apt-get update \
    && apt-get install -y postgresql-14-postgis-3 \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# add user with UID defined in .env
# skip, if UID already exists (e.g. postgres/1000)
ARG UID=1000
RUN adduser --uid ${UID} --disabled-password tsm || exit 0

# Adjust owner of postgres data directory
RUN chown ${UID} /var/lib/postgresql

# switch to user with UID
USER ${UID}