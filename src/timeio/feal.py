from __future__ import annotations

import atexit
from functools import lru_cache
from typing import Any, Self

import pandas as pd
import psycopg
from psycopg import Connection, conninfo
from psycopg.rows import dict_row

import logging

logger = logging.getLogger("frontend-AL")

"""
FEAL - Front End Abstraction Layer

This file provide a convenient way to access the (meta) data 
from the frontend. Currently this is a simple wrapper to access
the configDB, but this will most probalbly change in the near 
future.
"""


class ObjectNotFound(Exception):
    pass


def to_camelcase(s: str) -> str:
    return "".join(map(str.capitalize, s.split("_")))  # type: ignore


def _property(query: str, attr: str, cls: type[Base]):
    """Return a property, with a getter that returns another Model"""

    class Getter(property):

        def __init__(self):
            self._cache_miss = False
            super().__init__()

        @lru_cache()
        def _get_cached(self, instance, owner: type | None = None):
            self._cache_miss = True
            return self._get(instance, owner)

        def _get(self, instance, owner: type | None = None):
            res = instance._fetchone(instance._conn, query, getattr(instance, attr))
            if not res:
                raise ObjectNotFound(f"No {cls.__name__} found for {instance}")
            return cls.from_parent(res, instance)

        def __get__(self, instance, owner: type | None = None):
            if instance._cache:
                self._cache_miss = False
                res = self._get_cached(instance, owner)
                logger.debug(
                    f"CACHE %s: %s",
                    "MISS" if self._cache_miss else "HIT",
                    cls._table_name,
                )
                return res
            return self._get(instance, owner)

    return Getter()


def set_global_dsn(dsn: str):
    Base._dsn = dsn


class Base:
    _dsn: str | None = None
    __connection: Connection
    _table_name: str = "<not set>"
    _protected_attrs = frozenset()

    def __init__(self, attrs, conn: Connection, cache: bool):
        self._attrs = attrs
        self._conn = conn
        self._cache = cache

    @classmethod
    def from_parent(cls, res, parent: Base):
        return cls(res, parent._conn, parent._cache)

    def __repr__(self):
        attrs = self._attrs.copy()
        attrs.update({k: "*****" for k in self._protected_attrs})
        return f"{self.__class__.__name__}({str(attrs)[1:-1]})"

    def clear_cache(self):
        pass

    def get_conninfo(self):
        if self._conn is not None:
            return self._conn.info
        if self._dsn is not None:
            return conninfo.conninfo_to_dict(self._dsn)
        return None

    @classmethod
    def _get_connection(cls, dsn: str | None = None) -> Connection:
        # The user want a connection
        if dsn is not None:
            conn = psycopg.connect(dsn)
            atexit.register(lambda: conn.close() or logger.debug(f"closed {conn}"))
            return conn
        # Check for an existing class connection
        if conn := getattr(Base, "__connection", None):
            return conn
        # Create a class connection if possible
        if Base._dsn is None:
            raise ValueError(
                f"Either pass a psycopg.Connection by the keyword 'conn', "
                f"or use the function set_global_dsn() to set a DSN for "
                f"the whole python session."
            )
        Base.__connection = conn = psycopg.connect(Base._dsn)
        atexit.register(lambda: conn.close() or logger.debug(f"closed {conn}"))
        return Base.__connection

    @classmethod
    def _fetchall(cls, conn: Connection, query, *params):
        logger.debug("fetchall(%s, %s)", query, params)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    @classmethod
    def _fetchone(cls, conn: Connection, query, *params):
        logger.debug("fetchone(%s, %s)", query, params)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def to_dict(self) -> dict[str, Any]:
        return self._attrs.copy()



class Database(Base):
    _table_name = "database"
    _protected_attrs = frozenset({"password", "ro_password"})
    id: int = property(lambda self: self._attrs["id"])
    schema = property(lambda self: self._attrs["schema"])
    user = property(lambda self: self._attrs["user"])
    password = property(lambda self: self._attrs["password"])
    ro_user = property(lambda self: self._attrs["ro_user"])
    ro_password = property(lambda self: self._attrs["ro_password"])


class ExtAPIType(Base):
    _table_name = "ext_api_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class ExtAPI(Base):
    _table_name = "ext_api"
    id: int = property(lambda self: self._attrs["id"])
    api_type_id: int = property(lambda self: self._attrs["api_type_id"])
    sync_interval = property(lambda self: self._attrs["sync_interval"])
    sync_enabled = property(lambda self: self._attrs["sync_enabled"])
    settings = property(lambda self: self._attrs["settings"])
    api_type: ExtAPIType = _property("SELECT * FROM config_db.ext_api_type WHERE id = %s", "api_type_id", ExtAPIType)  # fmt: skip


class ExtSFTP(Base):
    _table_name = "ext_sftp"
    _protected_attrs = frozenset({"password", "ssh_priv_key"})
    id: int = property(lambda self: self._attrs["id"])
    uri = property(lambda self: self._attrs["uri"])
    path = property(lambda self: self._attrs["path"])
    user = property(lambda self: self._attrs["user"])
    password = property(lambda self: self._attrs["password"])
    ssh_priv_key = property(lambda self: self._attrs["ssh_priv_key"])
    ssh_pub_key = property(lambda self: self._attrs["ssh_pub_key"])
    sync_interval = property(lambda self: self._attrs["sync_interval"])
    sync_enabled = property(lambda self: self._attrs["sync_enabled"])


class FileParserType(Base):
    _table_name = "file_parser_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class FileParser(Base):
    _table_name = "file_parser"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])
    params = property(lambda self: self._attrs["params"])
    file_parser_type_id: int = property(lambda self: self._attrs["file_parser_type_id"])
    file_parser_type: FileParserType = _property(
        "SELECT * FROM config_db.file_parser_type WHERE id = %s",
        "file_parser_type_id",
        FileParserType,
    )


class IngestType(Base):
    _table_name = "ingest_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class MQTTDeviceType(Base):
    _table_name = "mqtt_device_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class MQTT(Base):
    _table_name = "mqtt"
    _protected_attrs = frozenset({"password", "password_hashed"})
    id: int = property(lambda self: self._attrs["id"])
    user = property(lambda self: self._attrs["user"])
    password = property(lambda self: self._attrs["password"])
    password_hashed = property(lambda self: self._attrs["password_hashed"])
    topic = property(lambda self: self._attrs["topic"])
    mqtt_device_type_id: int = property(lambda self: self._attrs["mqtt_device_type_id"])
    mqtt_device_type: MQTTDeviceType = _property(
        "SELECT * FROM config_db.mqtt_device_type WHERE id = %s",
        "mqtt_device_type_id",
        MQTTDeviceType,
    )


class Project(Base):
    _table_name = "project"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])
    uuid = property(lambda self: self._attrs["uuid"])
    database_id: int = property(lambda self: self._attrs["database_id"])
    database: Database = _property("SELECT * FROM config_db.database WHERE id = %s", "database_id", Database)  # fmt: skip

    @classmethod
    def from_uuid(cls, uuid: str, dsn: str | None = None, cache:bool=True):
        query = "select * from config_db.project where uuid::text = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, uuid)):
            raise ObjectNotFound(f"No Project found with {uuid=}")
        return Thing(res, conn, cache)

    @classmethod
    def from_name(cls, name: str, dsn: str | None = None, cache:bool=True):
        query = "select * from config_db.project where name = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, name)):
            raise ObjectNotFound(f"No Project found with {name=}")
        return Thing(res, conn, cache)

    @classmethod
    def from_id(cls, id: int, dsn: str | None = None, cache:bool=True):
        query = "select * from config_db.project where id = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, id)):
            raise ObjectNotFound(f"No Project found with {id=}")
        return Thing(res, conn, cache)

    def get_things(self) -> list[Thing]:
        query = "select * from config_db.thing where project_id = %s"
        conn = self._conn
        return [
            Thing.from_parent(attr, self) for attr in self._fetchall(conn, query, self.id)
        ]

    def get_qaqcs(self) -> list[QAQC]:
        query = "select * from config_db.qaqc where project_id = %s"
        return [QAQC.from_parent(attr, self) for attr in self._fetchall(self._conn, query, self.id)]


class QAQC(Base):
    _table_name = "qaqc"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])
    project_id: int = property(lambda self: self._attrs["project_id"])
    context_window = property(lambda self: self._attrs["context_window"])
    project: Project = _property("select * from config_db.project where id = %s", "project_id", Project)  # fmt: skip

    def get_tests(self) -> list[QAQCTest]:
        query = "select * from config_db.qaqc_test where qaqc_id = %s"
        conn = self._conn
        return [
            QAQCTest.from_parent(attr, self) for attr in self._fetchall(conn, query, self.id)
        ]


class QAQCTest(Base):
    _table_name = "qaqc_test"
    id: int = property(lambda self: self._attrs["id"])
    qaqc_id: int = property(lambda self: self._attrs["qaqc_id"])
    function = property(lambda self: self._attrs["function"])
    args = property(lambda self: self._attrs["args"])
    position = property(lambda self: self._attrs["position"])
    name = property(lambda self: self._attrs["name"])
    streams = property(lambda self: self._attrs["streams"])
    qaqc: QAQC = _property("select * from config_db.qaqc where id = %s", "qaqc_id", QAQC)  # fmt: skip


class S3Store(Base):
    _table_name = "s3_store"
    _protected_attrs = frozenset({"password"})
    id: int = property(lambda self: self._attrs["id"])
    user: str = property(lambda self: self._attrs["user"])
    password: str = property(lambda self: self._attrs["password"])
    bucket = property(lambda self: self._attrs["bucket"])
    filename_pattern = property(lambda self: self._attrs["filename_pattern"])
    file_parser_id: int = property(lambda self: self._attrs["file_parser_id"])
    file_parser: FileParser = _property("select * from config_db.file_parser where id = %s", "file_parser_id", FileParser)  # fmt: skip


class Thing(Base):
    _table_name = "thing"
    id: int = property(lambda self: self._attrs["id"])
    uuid = property(lambda self: self._attrs["uuid"])
    name = property(lambda self: self._attrs["name"])
    project_id: int = property(lambda self: self._attrs["project_id"])
    ingest_type_id: int = property(lambda self: self._attrs["ingest_type_id"])
    s3_store_id: int = property(lambda self: self._attrs["s3_store_id"])
    mqtt_id: int = property(lambda self: self._attrs["mqtt_id"])
    ext_sftp_id: int = property(lambda self: self._attrs["ext_sftp_id"])
    ext_api_id: int = property(lambda self: self._attrs["ext_api_id"])
    project: Project = _property("select * from config_db.project where id = %s", "project_id", Project)  # fmt: skip
    ingest_type: IngestType = _property("select * from config_db.ingest_type where id = %s", "ingest_type_id", IngestType)  # fmt: skip
    s3_store: S3Store = _property("select * from config_db.s3_store where id = %s", "s3_store_id", S3Store)  # fmt: skip
    mqtt: MQTT = _property("select * from config_db.mqtt where id = %s", "mqtt_id", MQTT)  # fmt: skip
    ext_sftp: ExtSFTP = _property("select * from config_db.ext_sftp where id = %s", "ext_sftp_id", ExtSFTP)  # fmt: skip
    ext_api: ExtAPI = _property("select * from config_db.ext_api where id = %s", "ext_api_id", ExtAPI)  # fmt: skip

    @classmethod
    def from_uuid(cls, uuid: str, dsn: str | None = None, cache:bool=True):
        query = "select * from config_db.thing where uuid::text = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, uuid)):
            raise ObjectNotFound(f"No Thing found with {uuid=}")
        return Thing(res, conn, cache)

    @classmethod
    def from_name(cls, name: str, dsn: str | None = None, cache:bool=True):
        query = "select * from config_db.thing where name = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, name)):
            raise ObjectNotFound(f"No Thing found with {name=}")
        return Thing(res, conn, cache)

    @classmethod
    def from_id(cls, id: int, dsn: str | None = None, cache:bool=True):
        query = "select * from config_db.thing where id = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, id)):
            raise ObjectNotFound(f"No Thing found with {id=}")
        return Thing(res, conn, cache)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    # b = B()
    # b.a()
    # print(C.cget())
    # print(C().cget())
    #
    dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    set_global_dsn(dsn)
    t = Thing.from_id(1)
    t = Thing.from_id(1, dsn=dsn).clear_cache()
    print(t.project.database)
    print(t.project.database)
    print(t.ext_sftp)
