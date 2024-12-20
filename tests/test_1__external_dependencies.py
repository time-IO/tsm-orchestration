#!/usr/bin/env python3
import os

import psycopg
import requests
import pytest
from tests_setup import *


@pytest.mark.parametrize(
    "dsn",
    [
        OBS_DB,
        CONF_DB,
        FE_DB,
        pytest.param(
            CV_DB,
            marks=pytest.mark.skipif(
                CV_ACCESS_TYPE != "db",
                reason=(
                    f"CV-Database is not tested, because "
                    f"$CV_ACCESS_TYPE is not set to 'db'"
                ),
            ),
        ),
        pytest.param(
            SMS_DB,
            marks=pytest.mark.skipif(
                SMS_ACCESS_TYPE != "db",
                reason=(
                    f"SMS-Database is not tested, because "
                    f"$SMS_ACCESS_TYPE is not set to 'db'"
                ),
            ),
        ),
    ],
)
def test_postgres_DBs_online(dsn):
    conn: psycopg.Connection
    with psycopg.connect(dsn) as conn:
        one = conn.execute("select 1").fetchone()
        assert one is not None and one[0] == 1


@pytest.mark.skipif(
    SMS_ACCESS_TYPE != "api",
    reason=f"SMS API is not tested, because $SMS_ACCESS_TYPE is not set to 'api'",
)
def test_sms_api_online():
    resp = requests.head(SMS_API_URL, timeout=1)
    resp.raise_for_status()


@pytest.mark.skipif(
    CV_ACCESS_TYPE != "api",
    reason=f"CV API is not tested, because $CV_ACCESS_TYPE is not set to 'api'",
)
def test_cv_api_online():
    resp = requests.head(CV_API_URL, timeout=1)
    resp.raise_for_status()
