#!/usr/bin/env python3
from __future__ import annotations

import logging
import threading
import urllib.request
from functools import partial
from typing import Any, Callable, Literal

import psycopg
import psycopg2
import psycopg2.extensions
import requests
from psycopg import Connection, conninfo
from psycopg.rows import dict_row

import timeio.parser as parser
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

    def ping(self, conn: Connection | None = None):
        try:
            if conn is not None:
                conn.execute("")
            else:
                with self.connection() as conn:
                    conn.execute("")
        except psycopg.errors.DatabaseError as e:
            raise ConnectionError(f"Ping to {self.name} failed. ({self.info})") from e


class ConfigDB(Database):
    name = "configDB"

    def get_parser(self, thing_uuid) -> parser.FileParser:
        """Returns parser-type-name and parser-parameter"""
        query = (
            "select fpt.name, fp.params from thing t "
            "join s3_store s3 on t.s3_store_id = s3.id "
            "join file_parser fp on s3.file_parser_id = fp.id "
            "join file_parser_type fpt on fp.file_parser_type_id = fpt.id "
            "where t.uuid = %s"
        )
        with self.connection() as conn:
            p_type, p_params = conn.execute(query, [thing_uuid]).fetchone()  # noqa
        return parser.get_parser(p_type, p_params)

    def get_mqtt_parser(self, thing_uuid) -> parser.MqttDataParser:
        query = (
            "select mdt.name from thing t join mqtt m on t.mqtt_id = m.id "
            "join mqtt_device_type mdt on m.mqtt_device_type_id = mdt.id "
            "where t.uuid = %s"
        )
        with self.connection() as conn:
            dev_type = conn.execute(query, [thing_uuid]).fetchone()  # noqa

        return parser.get_parser(dev_type, None)

    def get_thing_uuid(self, by: Literal["bucket", "mqtt_user"], value) -> str | None:
        # fmt: off
        by_map = {
            "bucket": "select t.uuid from thing t join s3_store s3 on "
                      "t.s3_store_id = s3.id where s3.bucket = %s",
            "mqtt_user": 'select t.uuid from mqtt m join thing t on '
                         'm.id = t.mqtt_id where m."user" = %s',
        }
        # fmt: on
        logging.debug(f"get thing uuid for {by}={value}")
        if query := by_map.get(by):
            with self.connection() as conn:
                res = conn.execute(query, [value]).fetchone()
                if res is None:
                    raise DataNotFoundError(f"No thing for {by}: {value}")
                uuid = res[0]
                logging.debug(f"got thing {uuid}")
                return uuid
        raise ValueError("Argument 'by' must be one of 'bucket' or 'mqtt_user'")

    def get_s3_store(self, thing_uuid):
        query = (
            "select s3s.* from config_db.s3_store s3s join "
            "thing t on s3s.id = t.s3_store_id where t.uuid = %s"
        )
        with self.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                return cur.execute(query, [thing_uuid]).fetchone()


class DBapi:

    def __init__(self, base_url):
        self.base_url = base_url
        self.ping_dbapi()

    def ping_dbapi(self):
        """
        Test the health endpoint of the given url.

        Added in version 0.4.0
        """
        with urllib.request.urlopen(f"{self.base_url}/health") as resp:
            if not resp.status == 200:
                raise ConnectionError(
                    f"Failed to ping. HTTP status code: {resp.status}"
                )

    def upsert_observations(self, thing_uuid: str, observations: list[dict[str, Any]]):
        url = f"{self.base_url}/observations/upsert/{thing_uuid}"
        response = requests.post(url, json={"observations": observations})
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"upload to {thing_uuid} failed with "
                f"{response.reason} and {response.text}"
            )


class ReentrantConnection:
    """
    Workaround for stale connections.
    Stale connections might happen for different reasons, for example, when
    a timeout occur, because the connection was not used for some time or
    the database service restarted.
    """

    # in seconds
    TIMEOUT = 2.0
    logger = logging.getLogger("ReentrantConnection")

    def __init__(
        self, dsn=None, connection_factory=None, cursor_factory=None, **kwargs
    ):

        # we use a nested function to hide credentials
        def _connect(_self) -> None:
            _self._conn = psycopg2.connect(
                dsn, connection_factory, cursor_factory, **kwargs
            )

        self._conn: psycopg2.extensions.connection | None = None
        self._connect = _connect
        self._lock = threading.RLock()

    def _is_alive(self) -> bool:
        try:
            self._ping()
        except TimeoutError:
            self.logger.debug("Connection timed out")
            return False
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self.logger.debug("Connection seems stale")
            return False
        else:
            return True

    def _ping(self):
        if self._conn is None:
            raise ValueError("must call connect first")
        with self._conn as conn:
            # unfortunately there is no client side timeout
            # option, and we encountered spurious very long
            # Connection timeouts (>15 min)
            timer = threading.Timer(self.TIMEOUT, conn.cancel)
            timer.start()
            try:
                # also unfortunately there is no other way to check
                # if the db connection is still alive, other than to
                # send a (simple) query.
                with conn.cursor() as c:
                    c.execute("select 1")
                    c.fetchone()
                if timer.is_alive():
                    return
            finally:
                try:
                    timer.cancel()
                except Exception:
                    pass
            raise TimeoutError("Connection timed out")

    def reconnect(self) -> psycopg2.extensions.connection:
        with self._lock:
            if self._conn is None or not self._is_alive():
                try:
                    self._conn.close()  # noqa
                except Exception:
                    pass
                self.logger.debug("(re)connecting to database")
                self._connect(self)
                self._ping()
        return self._conn

    connect = reconnect

    def close(self) -> None:
        self._conn.close()
