from __future__ import annotations

import atexit
from typing import Any, Self, TypeVar, Type, Generic, Callable

import psycopg
from psycopg import Connection, conninfo
from psycopg.rows import dict_row

import logging

logger = logging.getLogger("frontend-AL")

"""
FEAL - Front End Abstraction Layer

This file provide a convenient way to access the (meta-) data 
from the frontend (Thing, Project, QC-Settings, etc.) Currently 
this is a simple wrapper to access the configDB, but this will 
most probably change in the near future.
"""


class ObjectNotFound(Exception):
    pass


def _property(query: str, id_attr: str, cls: type[Base]):
    """Return a property, with a getter that returns another Model"""

    class Getter(property):

        def __get__(self, obj: Base, owner: type[Base] | None = None):
            rhs_id = getattr(obj, id_attr)
            key = (cls, rhs_id)
            if cached := obj._cache_get(key):
                return cached
            res = obj._fetchone(obj._conn, query, rhs_id)
            if not res:
                raise ObjectNotFound(
                    f"No entry found for '{obj._table_name}.{cls._table_name}', "
                    f"with {obj}"
                )
            inst = cls._from_parent(res, obj)
            obj._cache_set(key, inst)
            return inst

    return Getter()


def set_global_dsn(dsn: str):
    Base._dsn = dsn


class Base:
    _dsn: str | None = None
    __connection: Connection
    _table_name: str = "<not set>"
    _protected_attrs = frozenset()

    def __init__(self, attrs, conn: Connection, caching: bool):
        """ Constructor for creating a new instance from scratch.

        See also Base._from_parent(), which create a new instance
        from and existing instance, in other words, from within
        an instance-method you should call _from_parent.
        """
        self._attrs = attrs
        self._conn = conn
        self._cache = {} if caching else None
        self._root = True

    @classmethod
    def _from_parent(cls, res, parent: Base) -> Base:
        """ Constructor for creating an instance from an existing instance.

        For creating a new instance from scratch, in other words,
        from within a classmethod call __init__, but from within
        an instance-method call this.
        """
        # Only the root class (Thing or
        instance = cls(res, parent._conn, False)
        instance._cache = parent._cache
        instance._root = False
        return instance

    def __repr__(self):
        attrs = self._attrs.copy()
        attrs.update({k: "*****" for k in self._protected_attrs})
        return f"{self.__class__.__name__}({str(attrs)[1:-1]})"

    def __del__(self):
        if self._root:
            logger.debug(f"closing db connection {self._conn}")
            self._conn.close()

    @classmethod
    def _get_connection(cls, dsn: str | None = None) -> Connection:
        # The user want a connection
        if dsn is not None:
            conn = psycopg.connect(dsn)
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

    @staticmethod
    def _fetchall(conn: Connection, query, *params):
        logging.getLogger("al-cache").debug("fetchall(%s, %s)", query, params)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    @staticmethod
    def _fetchone(conn: Connection, query, *params):
        logger.debug("fetchone(%s, %s)", query, params)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def _cache_get(self, key):
        if self._cache:
            hit = key in self._cache
            logger.debug("cache %s: %s", "HIT" if hit else "MISS", key)
            return self._cache.get(key, None)
        return None

    def _cache_set(self, key, value):
        if self._cache is not None:
            self._cache[key] = value

    def clear_cache(self):
        if self._cache:
            self._cache.clear()

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
    def from_uuid(cls, uuid: str, dsn: str | None = None, caching: bool = True):
        query = "select * from config_db.project where uuid::text = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, uuid)):
            raise ObjectNotFound(f"No Project found with {uuid=}")
        return Project(res, conn, caching)

    @classmethod
    def from_name(cls, name: str, dsn: str | None = None, caching: bool = True):
        query = "select * from config_db.project where name = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, name)):
            raise ObjectNotFound(f"No Project found with {name=}")
        return Project(res, conn, caching)

    @classmethod
    def from_id(cls, id: int, dsn: str | None = None, caching: bool = True):
        query = "select * from config_db.project where id = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, id)):
            raise ObjectNotFound(f"No Project found with {id=}")
        return Project(res, conn, caching)

    def get_things(self) -> list[Thing]:
        query = "select * from config_db.thing where project_id = %s"
        conn = self._conn
        return [
            Thing._from_parent(attr, self)
            for attr in self._fetchall(conn, query, self.id)
        ]

    def get_qaqcs(self) -> list[QAQC]:
        query = "select * from config_db.qaqc where project_id = %s"
        return [
            QAQC._from_parent(attr, self)
            for attr in self._fetchall(self._conn, query, self.id)
        ]


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
            QAQCTest._from_parent(attr, self)
            for attr in self._fetchall(conn, query, self.id)
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
    def from_uuid(cls, uuid: str, dsn: str | None = None, caching: bool = True):
        query = "select * from config_db.thing where uuid::text = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, uuid)):
            raise ObjectNotFound(f"No Thing found with {uuid=}")
        return Thing(res, conn, caching)

    @classmethod
    def from_name(cls, name: str, dsn: str | None = None, caching: bool = True):
        query = "select * from config_db.thing where name = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, name)):
            raise ObjectNotFound(f"No Thing found with {name=}")
        return Thing(res, conn, caching)

    @classmethod
    def from_id(cls, id: int, dsn: str | None = None, caching: bool = True):
        query = "select * from config_db.thing where id = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(conn, query, id)):
            raise ObjectNotFound(f"No Thing found with {id=}")
        return Thing(res, conn, caching)


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    set_global_dsn(dsn)
    t = Thing.from_id(1)
    # t = Thing.from_id(1)
    # t = Thing.from_id(1, dsn=dsn, caching=False)
    # t = Thing.from_id(1, dsn=dsn)
    print(t.project.database)
    print(t.project.database.id)
