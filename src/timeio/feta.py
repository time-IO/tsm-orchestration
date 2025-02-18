from __future__ import annotations

import atexit
import warnings
from typing import Any, Self, TypeVar, Type, Generic, Callable

import psycopg
from psycopg import Connection, sql
from psycopg.rows import dict_row
import logging

logger = logging.getLogger("feta")

"""
FETA - Front End Thing Abstraction 

This file provide a convenient way to access the (meta-) data 
from the frontend (Thing, Project, QC-Settings, etc.) Currently 
this is a simple wrapper to access the configDB, but this will 
most probably change in the near future.
"""

_cfgdb = "config_db"


class ObjectNotFound(Exception):
    pass


def _property(query: str, id_attr: str, cls: type[Base]):
    """Return a property, with a getter that returns another Model"""

    class Getter(property):

        def __get__(self, obj: Base | None, owner: type[Base] | None = None):
            if obj is None:
                return self
            rhs_id = getattr(obj, id_attr)
            key = (cls, rhs_id)
            if cached := obj._cache_get(key):
                return cached
            res = obj._fetchall(obj._conn, query, rhs_id)
            if not res:
                raise ObjectNotFound(
                    f"No entry found for '{obj._table_name}.{cls._table_name}', "
                    f"with {obj}"
                )
            if len(res) > 1:
                warnings.warn(
                    f"Got multiple results from {_cfgdb}.{cls._table_name} "
                    f"for {id_attr}={rhs_id}. The returned object will be "
                    f"created from the first result."
                )
            inst = cls._from_parent(res[0], obj)
            obj._cache_set(key, inst)
            return inst

    return Getter()


def connect(dsn: str, **kwargs):
    """
    Globally connect feta with a DB.

    The connection i valid for the whole python session,
    to create a connection on creation of objects, use
    the dsn argument with the classmethods.
    For example `Thing.from_id(1, dsn=...)`

    :param dsn: connection string
    :param kwargs: kwargs are directly passed to psycopg.connect()
    """
    Base._set_global_connection(dsn, **kwargs)


class Base:
    __cls_connection: Connection | None = None
    _table_name: str = "<not set>"
    _protected_values = frozenset()

    def __init__(self, attrs, conn: Connection, caching: bool):
        """Constructor for creating a new Base instance from scratch.

        See also Base._from_parent(), which create a new instance
        from and existing Base instance, in other words, from within
        an instance-method you should call _from_parent.
        """
        self._attrs = attrs
        self._conn = conn
        self._cache = {} if caching else None
        self._root = True

    @classmethod
    def _from_parent(cls, res, parent: Base) -> Base:
        """Constructor for creating an instance from an existing Base instance.

        For creating a new instance from scratch, in other words,
        from within a classmethod call __init__, but from within
        an instance-method call this.
        """
        # Only the root class
        instance = cls(res, parent._conn, False)
        instance._cache = parent._cache
        instance._root = False
        return instance

    def __repr__(self):
        attrs = self._attrs.copy()
        attrs.update({k: "*****" for k in self._protected_values})
        return f"{self.__class__.__name__}({str(attrs)[1:-1]})"

    def __del__(self):
        if self._root:
            # The class connection is registered with atexit
            # to be closed on program exit.
            # see also Base._set_global_connection()
            if self._conn == self.__cls_connection:
                return
            logger.debug(f"Closing instance connection {self._conn}")
            self._conn.close()

    @classmethod
    def _set_global_connection(cls, dsn, **kwargs):
        cls.__cls_connection = conn = psycopg.connect(dsn, **kwargs)
        logger.debug(f"Opened global DB connection {conn}")

        def close_global_connection():
            conn.close()
            logger.debug(f"Closed global DB connection {conn}")

        atexit.register(close_global_connection)

    @classmethod
    def _get_connection(cls, dsn: str | None = None, **kwargs) -> Connection:
        # The user want a connection
        if dsn is not None:
            conn = psycopg.connect(dsn, **kwargs)
            return conn
        # Check for an existing class connection
        if cls.__cls_connection is not None:
            return cls.__cls_connection
        raise ValueError(
            f"Either pass the keyword argument 'dsn', or use the "
            f"function feta.connect() to set a global connection "
            f"for all FETA classes."
        )

    @staticmethod
    def _fetchall(conn: Connection, query, *params):
        logger.debug("fetchall(%s, %s)", query, params)
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
            logging.getLogger("feta-cache").debug(
                "cache %s: %s", "HIT" if hit else "MISS", key
            )
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

    # Each table has a PK column, that is named 'id'. That
    # is why we can safely add this to EVERY subclass.
    @classmethod
    def from_id(
        cls: Type[Self],
        id_: int,
        dsn: str | None = None,
        caching: bool = True,
        **kwargs,
    ) -> Self:
        """
        Fetch a new object by its ID.

        :param id_: The id of the object.
        :param dsn: Postgres connection string to make a DB connection
            with `psycopg.connect()`
        :param caching: If `True` (default) the object is cached and
            subsequently lookups will use the cached object. If `False`,
            the object is always fetched from its source (DB table).
        :param kwargs: All kwargs are passed on to the function `psycopg.connection`.
        :return: Returns an instance of a subclass of `feta.Base`
        """
        tab = sql.Identifier(_cfgdb, cls._table_name)
        query = sql.SQL("select * from {tab} where id = %s").format(tab=tab)
        conn = cls._get_connection(dsn, **kwargs)
        if not (res := cls._fetchall(conn, query, id_)):
            raise ObjectNotFound(f"No {cls.__name__} found for id={id_}")
        if len(res) > 1:
            warnings.warn(
                f"Got multiple results from {_cfgdb}.{cls._table_name} "
                f"for id={id_}. The returned object will be created from "
                f"the first result."
            )
        return cls(res[0], conn, caching)


class FromNameMixin:
    @classmethod
    def from_name(
        cls: Type[Self],
        name: str,
        dsn: str | None = None,
        caching: bool = True,
        **kwargs,
    ) -> Self:
        """
        Create a new object from its name.

        :param name: The name of the object.
        :param dsn: Postgres connection string to make a DB connection
            with `psycopg.connect()`
        :param caching: If `True` (default) the object is cached and
            subsequently lookups will use the cached object. If `False`,
            the object is always fetched from its source (DB table).
        :param kwargs: All kwargs are passed on to the function `psycopg.connection`.
        :return: Returns an instance of a subclass of `feta.Base`
        """
        tab = sql.Identifier(_cfgdb, cls._table_name)
        query = sql.SQL("select * from {tab} where name = %s").format(tab=tab)
        conn = cls._get_connection(dsn, **kwargs)
        if not (res := cls._fetchall(conn, query, name)):
            raise ObjectNotFound(f"No {cls.__name__} found with {name=}")
        if len(res) > 1:
            warnings.warn(
                f"Got multiple results from {_cfgdb}.{cls._table_name} "
                f"for {name=}. The returned object will be created from "
                f"the first result."
            )
        return cls(res[0], conn, caching)


class FromUUIDMixin:
    @classmethod
    def from_uuid(
        cls: Type[Self],
        uuid: str,
        dsn: str | None = None,
        caching: bool = True,
        **kwargs,
    ) -> Self:
        """
        Create a new object by its UUID.

        :param uuid: The UUID of the object.
        :param dsn: Postgres connection string to make a DB connection
            with `psycopg.connect()`
        :param caching: If `True` (default) the object is cached and
            subsequently lookups will use the cached object. If `False`,
            the object is always fetched from its source (DB table).
        :param kwargs: All kwargs are passed on to the function `psycopg.connection`.
        :return: Returns an instance of a subclass of `feta.Base`
        """
        tab = sql.Identifier(_cfgdb, cls._table_name)
        query = sql.SQL("select * from {tab} where uuid::text = %s").format(tab=tab)
        conn = cls._get_connection(dsn, **kwargs)
        if not (res := cls._fetchall(conn, query, uuid)):
            raise ObjectNotFound(f"No {cls.__name__} found for {uuid=}")
        if len(res) > 1:
            warnings.warn(
                f"Got multiple results from {_cfgdb}.{cls._table_name} "
                f"for {uuid=}. The returned object will be created from "
                f"the first result."
            )
        return cls(res[0], conn, caching)


class IngestType(Base, FromNameMixin):
    _table_name = "ingest_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class FileParserType(Base, FromNameMixin):
    _table_name = "file_parser_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class MQTTDeviceType(Base, FromNameMixin):
    _table_name = "mqtt_device_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class ExtAPIType(Base, FromNameMixin):
    _table_name = "ext_api_type"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])


class Database(Base):
    _table_name = "database"
    _protected_values = frozenset({"password", "ro_password"})
    id: int = property(lambda self: self._attrs["id"])
    schema = property(lambda self: self._attrs["schema"])
    user = property(lambda self: self._attrs["user"])
    ro_user = property(lambda self: self._attrs["ro_user"])

    # thing.Datebase interface
    username = user
    password = property(lambda self: self._attrs["password"])
    ro_username = ro_user
    ro_password = property(lambda self: self._attrs["ro_password"])
    # url = None  # TODO: missing in configDB
    # ro_url = None  # TODO: missing in configDB


class ExtAPI(Base):
    _table_name = "ext_api"
    id: int = property(lambda self: self._attrs["id"])
    api_type_id: int = property(lambda self: self._attrs["api_type_id"])
    sync_enabled = property(lambda self: self._attrs["sync_enabled"])

    # thing.ExternalApi interface
    enabled = sync_enabled
    api_type: ExtAPIType = _property(f"SELECT * FROM {_cfgdb}.ext_api_type WHERE id = %s", "api_type_id", ExtAPIType)  # fmt: skip
    sync_interval = property(lambda self: self._attrs["sync_interval"])
    settings = property(lambda self: self._attrs["settings"])


class ExtSFTP(Base):
    _table_name = "ext_sftp"
    _protected_values = frozenset({"password", "ssh_priv_key"})
    id: int = property(lambda self: self._attrs["id"])
    user = property(lambda self: self._attrs["user"])
    ssh_priv_key = property(lambda self: self._attrs["ssh_priv_key"])
    ssh_pub_key = property(lambda self: self._attrs["ssh_pub_key"])
    sync_enabled = property(lambda self: self._attrs["sync_enabled"])

    # thing.ExternalSFTP interface
    enabled = sync_enabled
    uri = property(lambda self: self._attrs["uri"])
    path = property(lambda self: self._attrs["path"])
    username = user
    password = property(lambda self: self._attrs["password"])
    sync_interval = property(lambda self: self._attrs["sync_interval"])
    public_key = ssh_pub_key


class FileParser(Base):
    _table_name = "file_parser"
    id: int = property(lambda self: self._attrs["id"])
    name = property(lambda self: self._attrs["name"])
    params = property(lambda self: self._attrs["params"])
    file_parser_type_id: int = property(lambda self: self._attrs["file_parser_type_id"])
    file_parser_type: FileParserType = _property(
        f"SELECT * FROM {_cfgdb}.file_parser_type WHERE id = %s",
        "file_parser_type_id",
        FileParserType,
    )


class MQTT(Base):
    _table_name = "mqtt"
    _protected_values = frozenset({"password", "password_hashed"})
    id: int = property(lambda self: self._attrs["id"])
    user = property(lambda self: self._attrs["user"])
    password = property(lambda self: self._attrs["password"])
    password_hashed = property(lambda self: self._attrs["password_hashed"])
    topic = property(lambda self: self._attrs["topic"])
    mqtt_device_type_id: int = property(lambda self: self._attrs["mqtt_device_type_id"])
    mqtt_device_type: MQTTDeviceType = _property(
        f"SELECT * FROM {_cfgdb}.mqtt_device_type WHERE id = %s",
        "mqtt_device_type_id",
        MQTTDeviceType,
    )


class S3Store(Base):
    _table_name = "s3_store"
    _protected_values = frozenset({"password"})
    id: int = property(lambda self: self._attrs["id"])
    user: str = property(lambda self: self._attrs["user"])
    bucket = property(lambda self: self._attrs["bucket"])
    file_parser_id: int = property(lambda self: self._attrs["file_parser_id"])
    file_parser: FileParser = _property(f"select * from {_cfgdb}.file_parser where id = %s", "file_parser_id", FileParser)  # fmt: skip

    # thing.RawDataStorage interface
    username = user
    password: str = property(lambda self: self._attrs["password"])
    bucket_name = bucket
    filename_pattern = property(lambda self: self._attrs["filename_pattern"])


class Project(Base, FromNameMixin, FromUUIDMixin):
    _table_name = "project"
    id: int = property(lambda self: self._attrs["id"])
    database_id: int = property(lambda self: self._attrs["database_id"])
    database: Database = _property(f"SELECT * FROM {_cfgdb}.database WHERE id = %s", "database_id", Database)  # fmt: skip

    # thing.Project interface
    uuid = property(lambda self: self._attrs["uuid"])
    name = property(lambda self: self._attrs["name"])

    def get_things(self) -> list[Thing]:
        query = f"select * from {_cfgdb}.thing where project_id = %s"
        conn = self._conn
        return [
            Thing._from_parent(attr, self)
            for attr in self._fetchall(conn, query, self.id)
        ]

    def get_qaqcs(self) -> list[QAQC]:
        query = f"select * from {_cfgdb}.qaqc where project_id = %s"
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
    project: Project = _property(f"select * from {_cfgdb}.project where id = %s", "project_id", Project)  # fmt: skip

    def get_tests(self) -> list[QAQCTest]:
        query = f"select * from {_cfgdb}.qaqc_test where qaqc_id = %s"
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
    qaqc: QAQC = _property(f"select * from {_cfgdb}.qaqc where id = %s", "qaqc_id", QAQC)  # fmt: skip


class Thing(Base, FromNameMixin, FromUUIDMixin):
    _table_name = "thing"
    project_id: int = property(lambda self: self._attrs["project_id"])
    s3_store_id: int = property(lambda self: self._attrs["s3_store_id"])
    ingest_type_id: int = property(lambda self: self._attrs["ingest_type_id"])
    mqtt_id: int = property(lambda self: self._attrs["mqtt_id"])
    ext_sftp_id: int = property(lambda self: self._attrs["ext_sftp_id"])
    ext_api_id: int = property(lambda self: self._attrs["ext_api_id"])
    ingest_type: IngestType = _property(f"select * from {_cfgdb}.ingest_type where id = %s", "ingest_type_id", IngestType)  # fmt: skip
    s3_store: S3Store = _property(f"select * from {_cfgdb}.s3_store where id = %s", "s3_store_id", S3Store)  # fmt: skip
    mqtt: MQTT = _property(f"select * from {_cfgdb}.mqtt where id = %s", "mqtt_id", MQTT)  # fmt: skip
    ext_sftp: ExtSFTP = _property(f"select * from {_cfgdb}.ext_sftp where id = %s", "ext_sftp_id", ExtSFTP)  # fmt: skip
    ext_api: ExtAPI = _property(f"select * from {_cfgdb}.ext_api where id = %s", "ext_api_id", ExtAPI)  # fmt: skip

    # thing.Thing interface
    id: int = property(lambda self: self._attrs["id"])
    uuid = property(lambda self: self._attrs["uuid"])
    name = property(lambda self: self._attrs["name"])
    project: Project = _property(f"select * from {_cfgdb}.project where id = %s", "project_id", Project)  # fmt: skip
    database: Database = property(lambda self: self.project.database)
    raw_data_storage = s3_store
    external_sftp = ext_sftp
    external_api = ext_api
    description = None  # TODO: missing in configDB
