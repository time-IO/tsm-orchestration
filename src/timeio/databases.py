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
