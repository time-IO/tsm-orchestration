#!/usr/bin/env python3
from __future__ import annotations

import logging
import json
import threading
import urllib.request
from functools import partial
from typing import Any, Callable
from datetime import datetime, timezone

import psycopg
import requests
from psycopg import Connection, conninfo

from timeio.errors import DataNotFoundError


class Database:
    name = "database"

    def __init__(self, dsn: str):
        self.info = conninfo.conninfo_to_dict(dsn)
        self.info.pop("password")
        self.__dsn = dsn
        self.ping()

    @property
    def connection(self) -> Callable[[], psycopg.Connection]:
        return partial(psycopg.connect, self.__dsn)

    def ping(self, conn: Connection | None = None) -> None:
        try:
            if conn is not None:
                conn.execute("")
            else:
                with self.connection() as conn:
                    conn.execute("")
        except psycopg.errors.DatabaseError as e:
            raise ConnectionError(f"Ping to {self.name} failed. ({self.info})") from e


class DBapi:

    def __init__(self, base_url, auth_token):
        self.base_url = base_url
        self.auth_token = auth_token
        self.ping_dbapi()

    def ping_dbapi(self) -> None:
        """
        Test the health endpoint of the given url.

        Added in version 0.4.0
        """
        with urllib.request.urlopen(f"{self.base_url}/health") as resp:
            if not resp.status == 200:
                raise ConnectionError(
                    f"Failed to ping. HTTP status code: {resp.status}"
                )

    def upsert_observations(
        self, thing_uuid: str, observations: list[dict[str, Any]]
    ) -> None:
        url = f"{self.base_url}/observations/upsert/{thing_uuid}"
        response = requests.post(
            url,
            json={"observations": observations},
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        response.raise_for_status()

    def insert_mqtt_message(self, thing_uuid: str, message: Any) -> None:
        url = f"{self.base_url}/things/{thing_uuid}/mqtt_message/insert"
        response = requests.post(
            url,
            json={
                "message": (
                    json.dumps(message)
                    if isinstance(message, dict)
                    else str(message)
                ),
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        response.raise_for_status()
