#!/usr/bin/env python3

from __future__ import annotations

import datetime
import typing as _t

JsonScalarT = _t.Union[str, int, float, bool, None]
JsonArrayT = list["JsonT"]
JsonObjectT = dict[str, "JsonT"]
JsonT = _t.Union[JsonScalarT, JsonArrayT, JsonObjectT]

DbScalarT = _t.Union[str, bool, int, float, JsonT, datetime.datetime.timestamp]
DbRowT = tuple[DbScalarT, ...]


class MqttPayload:

    class QaqcConfigV1_T(_t.TypedDict):
        version: _t.Literal[1]
        name: str
        project_uuid: str
        context_window: str
        tests: list[MqttPayload.QaqcTestT]

    class QaqcConfigV2_T(_t.TypedDict):
        version: _t.Literal[2]
        name: str
        project_uuid: str
        context_window: str
        functions: list[MqttPayload.QaqcFunctionT]

    class QaqcTestT(_t.TypedDict, total=True):
        function: str
        kwargs: dict[str, _t.Any]
        position: int

    class QaqcFunctionT(_t.TypedDict, total=True):
        name: str
        func_id: str
        kwargs: dict[str, _t.Any]
        datastreams: list[MqttPayload.QaqcFuncStreamsT]

    class QaqcFuncStreamsT(_t.TypedDict):
        arg_name: str
        thing_sta_id: int | None
        sta_stream_id: int | None


class ConfDB:

    class DatabaseT(_t.TypedDict):
        id: int
        schema: str
        user: str
        password: str
        ro_user: str
        re_password: str

    class ExtApiT(_t.TypedDict):
        id: int
        api_type_id: int
        sync_interval: int
        sync_enabled: bool
        settings: JsonT | None

    class ExtApiTypeT(_t.TypedDict):
        id: int
        name: str

    class ExtSFTP_T(_t.TypedDict):
        id: int
        uri: str
        path: str
        user: str
        password: str | None
        ssh_priv_key: int
        ssh_pub_key: int
        sync_interval: int
        sync_enabled: bool

    class FileParserT(_t.TypedDict):
        id: int
        file_parser_type_id: int
        name: str
        params: JsonT | None

    class FileParserTypeT(_t.TypedDict):
        id: int
        name: str

    class IngestTypeT(_t.TypedDict):
        id: int
        name: str

    class MqttT(_t.TypedDict):
        id: int
        user: str
        password: str
        password_hashed: str
        topic: str | None
        mqtt_device_type_id: int | None

    class MqttDeviceTypeT(_t.TypedDict):
        id: int
        name: str

    class ProjectT(_t.TypedDict):
        id: int
        name: str
        uuid: str
        database_id: int

    class QaqcT(_t.TypedDict):
        id: int
        name: str
        project_id: int
        context_window: str

    class QaqcTestT(_t.TypedDict):
        id: int
        qaqc_id: int
        function: str
        args: JsonT | None
        position: int | None
        name: str | None
        streams: list[ConfDB.QaqcTestStreamT] | None

    class QaqcTestStreamT(_t.TypedDict):
        arg_name: str
        sta_thing_id: int | None
        sta_stream_id: int | None

    class S3_StoreT(_t.TypedDict):
        id: int
        user: str
        password: str
        bucket: str
        filename_pattern: str | None
        file_parser_id: int

    class ThingT(_t.TypedDict):
        id: int
        uuid: int
        name: str
        project_id: int
        ingest_type_id: int
        s3_store_id: int
        mqtt_id: int
        ext_sftp_id: int | None
        ext_api_id: int | None
