from __future__ import annotations

import atexit
from functools import lru_cache
from typing import Any

import psycopg
from psycopg import Connection, conninfo
from psycopg.rows import dict_row

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


def _property(query: str, attr: str, cls: type):
    """Return a property, with a getter that returns another Model"""

    def fget(self: Base) -> Base:
        res = self._fetchone(query, getattr(self, attr))
        if not res:
            raise ObjectNotFound(f"No {cls.__name__} found for {self}")
        return cls(res)

    return property(fget)


def set_global_dsn(dsn: str):
    Base._dsn = dsn


class Base:
    _dsn: str | None = None
    __connection: Connection
    _protected_attrs = frozenset()

    def __init__(self, attrs, conn: Connection | None = None):
        self._conn = conn
        self._attrs = attrs

    def __repr__(self):
        attrs = self._attrs.copy()
        attrs.update({k: "*****" for k in self._protected_attrs})
        return f"{self.__class__.__name__}({str(attrs)[1:-1]})"

    def get_conninfo(self):
        if self._conn is not None:
            return self._conn.info
        if self._dsn is not None:
            return conninfo.conninfo_to_dict(self._dsn)
        return None

    def _get_connection(cls, dsn: str | None = None) -> Connection:
        if dsn is None:
            return cls._get_internal_connection()

    @classmethod
    # @lru_cache
    def _get_internal_connection(cls, conn: Connection | None = None) -> Connection:
        # We got a user created connection
        if conn is not None:
            if not isinstance(conn, Connection):
                raise TypeError(f"conn must be a psycopg.Connection, not {type(conn)}")
            return conn

        if (conn := getattr(Base, "__connection", None)) is None:
            if Base._dsn is None:
                raise ValueError(
                    f"Either pass a psycopg.Connection by the keyword 'conn', "
                    f"or use the function set_global_dsn() to set a DSN for "
                    f"the whole python session."
                )
            Base.__connection = conn = psycopg.connect(Base._dsn)
            atexit.register(lambda: Base.__connection.close())
        return conn

    @classmethod
    def _fetchall(cls, query, *params, conn: Connection | None = None):
        conn = cls._get_connection(conn)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    @classmethod
    def _fetchone(cls, query, *params, conn: Connection | None = None):
        conn = cls._get_connection(conn)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def to_dict(self) -> dict[str, Any]:
        return self._attrs.copy()


class Database(Base):
    _protected_attrs = frozenset({"password", "ro_password"})

    id = property(lambda self: self._attrs["id"])
    schema = property(lambda self: self._attrs["schema"])
    user = property(lambda self: self._attrs["user"])
    password = property(lambda self: self._attrs["password"])
    ro_user = property(lambda self: self._attrs["ro_user"])
    ro_password = property(lambda self: self._attrs["ro_password"])


class ExtAPIType(Base):
    id = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class ExtAPI(Base):
    id = property(lambda self: self._attrs["id"])
    api_type_id = property(lambda self: self._attrs["api_type_id"])
    sync_interval = property(lambda self: self._attrs["sync_interval"])
    sync_enabled = property(lambda self: self._attrs["sync_enabled"])
    settings = property(lambda self: self._attrs["settings"])
    api_type: ExtAPIType = _property("SELECT * FROM config_db.ext_api_type WHERE id = %s", "api_type_id", ExtAPIType)  # fmt: skip


class ExtSFTP(Base):
    _protected_attrs = frozenset({"password", "ssh_priv_key"})
    id = property(lambda self: self._attrs["id"])
    uri = property(lambda self: self._attrs["uri"])
    path = property(lambda self: self._attrs["path"])
    user = property(lambda self: self._attrs["user"])
    password = property(lambda self: self._attrs["password"])
    ssh_priv_key = property(lambda self: self._attrs["ssh_priv_key"])
    ssh_pub_key = property(lambda self: self._attrs["ssh_pub_key"])
    sync_interval = property(lambda self: self._attrs["sync_interval"])
    sync_enabled = property(lambda self: self._attrs["sync_enabled"])


class FileParserType(Base):
    id = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class FileParser(Base):
    id = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])
    params = property(lambda self: self._attrs["params"])
    file_parser_type_id = property(lambda self: self._attrs["file_parser_type_id"])
    file_parser_type: FileParserType = _property(
        "SELECT * FROM config_db.file_parser_type WHERE id = %s",
        "file_parser_type_id",
        FileParserType,
    )


class IngestType(Base):
    id = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class MQTTDeviceType(Base):
    id = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class MQTT(Base):
    _protected_attrs = frozenset({"password", "password_hashed"})
    id = property(lambda self: self._attrs["id"])
    user = property(lambda self: self._attrs["user"])
    password = property(lambda self: self._attrs["password"])
    password_hashed = property(lambda self: self._attrs["password_hashed"])
    topic = property(lambda self: self._attrs["topic"])
    mqtt_device_type_id = property(lambda self: self._attrs["mqtt_device_type_id"])
    mqtt_device_type: MQTTDeviceType = _property(
        "SELECT * FROM config_db.mqtt_device_type WHERE id = %s",
        "mqtt_device_type_id",
        MQTTDeviceType,
    )


class Project(Base):
    id = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])
    uuid = property(lambda self: self._attrs["uuid"])
    database_id = property(lambda self: self._attrs["database_id"])
    database: Database = _property("SELECT * FROM config_db.database WHERE id = %s", "database_id", Database)  # fmt: skip

    @classmethod
    def from_uuid(cls, uuid, dsn: str | None = None):
        query = "select * from config_db.project where uuid::text = %s"
        if not (res := cls._fetchone(query, uuid, dsn=dsn)):
            raise ObjectNotFound(f"No Project found with {uuid=}")
        return Thing(res)

    @classmethod
    def from_name(cls, name, dsn: str | None = None):
        query = "select * from config_db.project where name = %s"
        if not (res := cls._fetchone(query, name, dsn=dsn)):
            raise ObjectNotFound(f"No Project found with {name=}")
        return Thing(res)

    @classmethod
    def from_id(cls, id, dsn: str | None = None):
        query = "select * from config_db.project where id = %s"
        if not (res := cls._fetchone(query, id, dsn=dsn)):
            raise ObjectNotFound(f"No Project found with {id=}")
        return Thing(res)

    def get_things(self) -> list[Thing]:
        query = "select * from config_db.thing where project_id = %s"
        return [Thing(attr) for attr in self._fetchall(query, self.id, dsn=dsn)]

    def get_qaqcs(self) -> list[QAQC]:
        query = "select * from config_db.qaqc where project_id = %s"
        return [QAQC(attr) for attr in self._fetchall(query, self.id, dsn=dsn)]


class QAQC(Base):
    id = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])
    project_id = property(lambda self: self._attrs["project_id"])
    context_window = property(lambda self: self._attrs["context_window"])
    project: Project = _property("select * from config_db.project where id = %s", "project_id", Project)  # fmt: skip

    def get_tests(self) -> list[QAQCTest]:
        query = "select * from config_db.qaqc_test where qaqc_id = %s"
        return [QAQCTest(attr) for attr in self._fetchall(query, self.id, dsn=dsn)]


class QAQCTest(Base):
    id = property(lambda self: self._attrs["id"])
    qaqc_id = property(lambda self: self._attrs["qaqc_id"])
    function = property(lambda self: self._attrs["function"])
    args = property(lambda self: self._attrs["args"])
    position = property(lambda self: self._attrs["position"])
    name = property(lambda self: self._attrs["name"])
    streams = property(lambda self: self._attrs["streams"])
    qaqc: QAQC = _property("select * from config_db.qaqc where id = %s", "qaqc_id", QAQC)  # fmt: skip


class S3Store(Base):
    _protected_attrs = frozenset({"password"})
    id = property(lambda self: self._attrs["id"])
    user: str = property(lambda self: self._attrs["user"])
    password: str = property(lambda self: self._attrs["password"])
    bucket = property(lambda self: self._attrs["bucket"])
    filename_pattern = property(lambda self: self._attrs["filename_pattern"])
    file_parser_id = property(lambda self: self._attrs["file_parser_id"])
    file_parser: FileParser = _property("select * from config_db.file_parser where id = %s", "file_parser_id", FileParser)  # fmt: skip


class Thing(Base):
    id = property(lambda self: self._attrs["id"])
    uuid = property(lambda self: self._attrs["uuid"])
    name = property(lambda self: self._attrs["name"])
    project_id = property(lambda self: self._attrs["project_id"])
    ingest_type_id = property(lambda self: self._attrs["ingest_type_id"])
    s3_store_id = property(lambda self: self._attrs["s3_store_id"])
    mqtt_id = property(lambda self: self._attrs["mqtt_id"])
    ext_sftp_id = property(lambda self: self._attrs["ext_sftp_id"])
    ext_api_id = property(lambda self: self._attrs["ext_api_id"])
    project: Project = _property("select * from config_db.project where id = %s", "project_id", Project)  # fmt: skip
    ingest_type: IngestType = _property("select * from config_db.ingest_type where id = %s", "ingest_type_id", IngestType)  # fmt: skip
    s3_store: S3Store = _property("select * from config_db.s3_store where id = %s", "s3_store_id", S3Store)  # fmt: skip
    mqtt: MQTT = _property("select * from config_db.mqtt where id = %s", "mqtt_id", MQTT)  # fmt: skip
    ext_sftp: ExtSFTP = _property("select * from config_db.ext_sftp where id = %s", "ext_sftp_id", ExtSFTP)  # fmt: skip
    ext_api: ExtAPI = _property("select * from config_db.ext_api where id = %s", "ext_api_id", ExtAPI)  # fmt: skip

    @classmethod
    def from_uuid(cls, uuid, dsn: str | None = None):
        query = "select * from config_db.thing where uuid::text = %s"
        if not (res := cls._fetchone(query, uuid, dsn=dsn)):
            raise ObjectNotFound(f"No Thing found with {uuid=}")
        return Thing(res)

    @classmethod
    def from_name(cls, name, dsn: str | None = None):
        query = "select * from config_db.thing where name = %s"
        if not (res := cls._fetchone(query, name, dsn=dsn)):
            raise ObjectNotFound(f"No Thing found with {name=}")
        return Thing(res)

    @classmethod
    def from_id(cls, id, dsn: str | None = None):
        query = "select * from config_db.thing where id = %s"
        conn = cls._get_connection(dsn)
        if not (res := cls._fetchone(query, id, conn=conn)):
            raise ObjectNotFound(f"No Thing found with {id=}")
        return Thing(res, conn=conn)


class A:

    @classmethod
    def a(cls):
        A.attr = "some a"

    @classmethod
    def cget(cls):
        return cls.attr

    def iget(self):
        return self.attr


class B(A):
    pass


class C(A):
    @classmethod
    def c(cls):
        cls.attr = "some b"


if __name__ == "__main__":
    # b = B()
    # b.a()
    # print(C.cget())
    # print(C().cget())
    #
    dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    # set_global_dsn(dsn)
    t = Thing.from_id(1, dsn=dsn)
    print(t.project.database)
    print(t.project.database.to_dict())
