#!/usr/bin/env python3
from common import getenv, mk_postgres_dsn


SMS_DB = None
SMS_API_URL = None
SMS_ACCESS_TYPE = getenv("SMS_ACCESS_TYPE")

if SMS_ACCESS_TYPE == "api":
    SMS_API_URL = (
        getenv("SMS_URL") + "backend/api/v1/"
    )  # TODO: missing var SMS_API_URL in .env
if SMS_ACCESS_TYPE == "db":
    SMS_DB = mk_postgres_dsn(
        getenv("SMS_DB_USER"),
        getenv("SMS_DB_PASSWORD"),
        getenv("SMS_DB_HOST"),
        getenv("SMS_DB_PORT", cast_to=int),
        getenv("SMS_DB_DB"),
    )

CV_DB = None
CV_API_URL = None
CV_ACCESS_TYPE = getenv("CV_ACCESS_TYPE")

if CV_ACCESS_TYPE == "api":
    CV_API_URL = getenv("CV_URL") + "api/v1"  # TODO: missing var CV_API_URL in .env
if CV_ACCESS_TYPE == "db":
    CV_DB = mk_postgres_dsn(
        getenv("CV_DB_USER"),
        getenv("CV_DB_PASSWORD"),
        getenv("CV_DB_HOST"),
        getenv("CV_DB_PORT", cast_to=int),
        getenv("CV_DB_DB"),
    )

OBS_DB = mk_postgres_dsn(
    getenv("CREATEDB_POSTGRES_USER"),
    getenv("CREATEDB_POSTGRES_PASSWORD"),
    getenv("CREATEDB_POSTGRES_HOST"),
    getenv("CREATEDB_POSTGRES_PORT", 5432, cast_to=int),  # TODO: missing var in .env !
    getenv("CREATEDB_POSTGRES_DATABASE"),
)

CONF_DB = mk_postgres_dsn(
    getenv("CONFIGDB_USER"),
    getenv("CONFIGDB_PASSWORD"),
    getenv("CONFIGDB_HOST"),
    getenv("CONFIGDB_PORT", cast_to=int),
    getenv("CONFIGDB_DB"),
)
FE_DB = mk_postgres_dsn(
    getenv("FRONTEND_POSTGRES_USER"),
    getenv("FRONTEND_POSTGRES_PASS"),
    getenv("FRONTEND_POSTGRES_HOST"),
    getenv("FRONTEND_POSTGRES_PORT", 5432, cast_to=int),  # TODO: missing var in .env !
    getenv("FRONTEND_POSTGRES_DB"),
)
