#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from functools import partial
from typing import Any, Callable, Literal
from datetime import datetime, timezone

import psycopg
import requests
from psycopg import Connection, conninfo

from timeio.typehints import TimestampT


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

    def delete_observations(
        self, thing_uuid: str, pos: str, start_date=TimestampT, end_date=TimestampT
    ):
        url = f"{self.base_url}/things/{thing_uuid}/datastreams/{pos}/observations"

        resp = requests.delete(
            url,
            params={"datetime_from": start_date, "datetime_to": end_date},
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        resp.raise_for_status()

    def upsert_observations(self, thing_uuid: str, observations: list[dict[str, Any]]):
        url = f"{self.base_url}/things/{thing_uuid}/datastreams/observations/upsert"

        resp = requests.post(
            url,
            json={"observations": observations},
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        resp.raise_for_status()

    def upsert_qc_labels(self, thing_uuid: str, qc_labels: list[dict[str, Any]]):
        url = f"{self.base_url}/things/{thing_uuid}/observations/qaqc"

        resp = requests.post(
            url,
            json={"qaqc_labels": qc_labels},
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        resp.raise_for_status()

    def insert_datastreams(
        self, thing_uuid: str, datastreams: list[dict[str, Any]], mutable: bool
    ) -> list[dict[Literal["position", "id", "status"], str]]:
        unique_pos = list(set([obs["datastream_pos"] for obs in datastreams]))
        datastreams = [{"position": pos, "mutable": mutable} for pos in unique_pos]
        url = f"{self.base_url}/things/{thing_uuid}/datastreams"
        resp = requests.post(
            url,
            json={"datastreams": datastreams},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        resp.raise_for_status()
        return [s | {"thing_uuid": thing_uuid} for s in resp.json()]

    def get_datastream(self, thing_uuid: str, pos: str):

        url = f"{self.base_url}/things/{thing_uuid}/datastreams/{pos}"
        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def get_datastream_observations(
        self,
        thing_uuid: str,
        pos: str,
        start_date: TimestampT | None = None,
        end_date: TimestampT | None = None,
        include_qc: bool = True,
    ):
        url = f"{self.base_url}/things/{thing_uuid}/datastreams/{pos}/observations"
        params = {"show_qc": include_qc}
        if start_date is not None:
            params["datetime_from"] = start_date
        if end_date is not None:
            params["datetime_to"] = end_date

        resp = requests.get(
            url,
            params=params,
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def upsert_observations_and_datastreams(
        self, thing_uuid: str, observations: list[dict[str, Any]], mutable: bool
    ):
        self.insert_datastreams(thing_uuid, observations, mutable)
        self.upsert_observations(thing_uuid, observations)

    def insert_mqtt_message(self, thing_uuid: str, message: Any) -> None:
        url = f"{self.base_url}/things/{thing_uuid}/mqtt_message/insert"
        resp = requests.post(
            url,
            json={
                "message": (
                    json.dumps(message) if isinstance(message, dict) else str(message)
                ),
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            },
            headers={
                "Authorization": f"Bearer {self.auth_token}",
            },
        )
        resp.raise_for_status()
