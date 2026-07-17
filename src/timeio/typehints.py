#!/usr/bin/env python3

from __future__ import annotations

import datetime
import typing as _t

import pandas as pd
from pandas._libs.tslibs.nattype import NaTType

JsonScalarT = _t.Union[str, int, float, bool, None]
JsonArrayT = list["JsonT"]
JsonObjectT = dict[str, "JsonT"]
JsonT = _t.Union[JsonScalarT, JsonArrayT, JsonObjectT]

DbScalarT = _t.Union[str, bool, int, float, JsonT, datetime.datetime.timestamp]
DbRowT = tuple[DbScalarT, ...]

TimestampT = datetime.datetime | pd.Timestamp | NaTType

v1 = 1
v2 = 2
v3 = 3
v4 = 4
v5 = 5


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

    class QaqcConfigV3_T(_t.TypedDict):
        version: _t.Literal[3]
        default: bool
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

    class UpdateThing(_t.TypedDict):
        version: _t.Literal[1] | None
        thing: str  # UUID of the thing

    class SyncExtApiT(_t.TypedDict):
        thing: str  # UUID of the thing
        datetime_from: str
        datetime_to: str

    class SyncExtSftpT(_t.TypedDict):
        thing: str  # UUID of the thing

    class SyncSmsT(_t.TypedDict):
        origin: str  # sms backend data or sms cv data

    class DataParsedV1(_t.TypedDict):
        version: _t.Literal[1] | None
        thing_uuid: str
        start_date: str
        end_date: str

    class DataParsedV2(_t.TypedDict):
        version: _t.Literal[2]
        project_uuid: str
        qc_settings_name: str
        start_date: str
        end_date: str


typedDict = _t.TypeVar("typedDict")


def check_dict_by_TypedDict(
    value: dict, expected: type[typedDict], name: str
) -> typedDict:
    """Check if all mandatory keys of the expected TypedDict are present in value.
    Returns the unmodified value. The return type is cast to the requested type.
    """
    missing = expected.__required_keys__ - value.keys()
    if missing:
        raise KeyError(f"{', '.join(missing)} are a mandatory keys for {name!r}")
    return _t.cast(expected, value)  # type: ignore
