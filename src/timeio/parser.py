#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import math
import re
import warnings

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from io import StringIO
from typing import Any, TypedDict, TypeVar, cast

import pandas as pd
from typing_extensions import Required

from timeio.common import ObservationResultType
from timeio.errors import ParsingError, ParsingWarning
from timeio.journaling import Journal
from timeio.typehints import JsonT

parsedT = TypeVar("parsedT")
journal = Journal("Parser")


def filter_lines(rawdata: str, skip: tuple | str) -> str:
    if isinstance(skip, str):
        skip = (skip,)
    pattern = "|".join(skip)
    return "\n".join(ln for ln in rawdata.splitlines() if not re.match(pattern, ln))


class ObservationPayloadT(TypedDict, total=False):
    phenomenon_time_start: str
    phenomenon_time_end: str
    result_time: Required[str]
    result_type: Required[int]
    result_number: float | int
    result_string: str
    result_boolean: bool
    result_json: JsonT
    result_latitude: float | int
    result_longitude: float | int
    result_altitude: float | int
    result_quality: JsonT
    valid_time_start: str
    valid_time_end: str
    parameters: JsonT
    datastream_pos: Required[str]


class Parser(ABC):
    @abstractmethod
    def do_parse(self, *args) -> parsedT:
        raise NotImplementedError

    @abstractmethod
    def to_observations(self, *args) -> list[ObservationPayloadT]:
        raise NotImplementedError


class FileParser(Parser):
    def __init__(self, settings: dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.settings = settings
        name = self.__class__.__name__
        self.logger.debug(f"parser settings in use with {name}: {self.settings}")

    @abstractmethod
    def do_parse(self, rawdata: Any) -> pd.DataFrame:
        raise NotImplementedError

    def to_observations(
        self, data: pd.DataFrame, origin: str
    ) -> list[ObservationPayloadT]:
        observations = []

        data.index.name = "result_time"
        data.index = data.index.strftime("%Y-%m-%dT%H:%M:%S%Z")

        to_process = [val for _, val in data.items()]

        while to_process:
            chunk = to_process.pop()
            col = str(chunk.name)
            if pd.api.types.is_numeric_dtype(chunk):
                chunk.name = "result_number"
                result_type = ObservationResultType.Number
            elif pd.api.types.is_bool_dtype(chunk):
                chunk.name = "result_bool"
                result_type = ObservationResultType.Bool
            elif pd.api.types.is_object_dtype(chunk):
                # we need to handle object columns with special care

                # try to seperate out numerical values to account for data (transmission) errors
                numeric_chunk = cast(pd.Series, pd.to_numeric(chunk, errors="coerce"))
                if numeric_chunk.isna().all():
                    # no numerical values found, we have a string only column
                    chunk.name = "result_string"
                    result_type = ObservationResultType.String
                else:
                    # numerical values found -> the column consists of mixed data types, currently
                    # we only distinguish between numerical and string values, this could be
                    # improved in the future
                    str_chunk = cast(
                        pd.Series, chunk.loc[numeric_chunk.isna()].str.strip()
                    )
                    to_process.extend((numeric_chunk, str_chunk))
                    continue
            else:
                raise ParsingError(
                    f"Data of type {chunk.dtype} is not supported. "
                    f"In {origin or 'datafile'}, column {col}"
                )

            # we don't want to write NaN
            chunk = chunk.dropna()
            # add metadata
            chunk = chunk.reset_index()
            chunk["result_type"] = result_type
            chunk["datastream_pos"] = str(col)
            chunk["parameters"] = json.dumps({"origin": origin, "column_header": col})

            observations.extend(chunk.to_dict(orient="records"))

        return observations


class CsvParser(FileParser):
    def _set_index(self, df: pd.DataFrame, timestamp_columns: dict) -> pd.DataFrame:

        date_columns = [d["column"] for d in timestamp_columns]
        date_format = " ".join([d["format"] for d in timestamp_columns])

        for c in date_columns:
            if c not in df.columns:
                raise ParsingError(f"Timestamp column {c} does not exist. ")

        index = reduce(
            lambda x, y: x + " " + y,
            [df[c].fillna("").astype(str).str.strip() for c in date_columns],
        )
        df = df.drop(columns=date_columns)

        index = pd.to_datetime(index, format=date_format, errors="coerce")
        if index.isna().any():
            nat = index.isna()
            warnings.warn(
                f"Could not parse {nat.sum()} of {len(index)} timestamps "
                f"with provided timestamp format {date_format!r}. First failing "
                f"timestamp: '{index[nat].iloc[0]}'",
                ParsingWarning,
            )
        index.name = None
        df.index = index
        return df

    def do_parse(self, rawdata: str) -> pd.DataFrame:
        """
        Parse rawdata string to pandas.DataFrame
        rawdata: the unparsed content
        NOTE:
            we need to preserve the original column numbering
        """
        settings = self.settings.copy()
        self.logger.info(settings)

        timestamp_columns = settings.pop("timestamp_columns")

        if "comment" in settings:
            rawdata = filter_lines(rawdata, settings.pop("comment"))

        try:
            df = pd.read_csv(StringIO(rawdata), **settings)
        except (pd.errors.EmptyDataError, IndexError):  # both indicate no data
            df = pd.DataFrame()

        # We always use positions as header
        df.columns = range(len(df.columns))

        # remove all-nan columns as artifacts
        df = df.dropna(axis=1, how="all")
        if df.empty:
            return pd.DataFrame(index=pd.DatetimeIndex([]))

        df = self._set_index(df, timestamp_columns)
        # remove rows with broken dates
        df = df.loc[df.index.notna()]

        self.logger.debug(f"data.shape={df.shape}")
        return df


# ============================================================
# Mqtt Parser
# ============================================================


@dataclass
class Observation:
    # This is a legacy class of the datastore_lib
    # see tsm_datastore_lib.Observation
    timestamp: datetime | str
    value: float | int | str | bool
    origin: str
    position: int
    header: str = ""

    def __post_init__(self):
        if self.value is None:
            raise ValueError("None is not allowed as observation value.")
        if math.isnan(self.value):
            raise ValueError("NaN is not allowed as observation value.")


class MqttDataParser(Parser):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__qualname__)

    @abstractmethod
    def do_parse(self, rawdata: Any, origin: str) -> list[Observation]:
        raise NotImplementedError

    def to_observations(
        self, data: list[Observation], thing_uuid: str
    ) -> list[ObservationPayloadT]:
        result = []
        for ob in data:
            if isinstance(ts := ob.timestamp, datetime):
                ts = ts.isoformat()
            obpay: ObservationPayloadT = {
                "result_time": str(ts),
                "datastream_pos": str(ob.position),
                "parameters": json.dumps(
                    {
                        "origin": ob.origin,
                        "column_header": ob.header,
                    }
                ),
            }
            if isinstance(ob.value, (float, int)):
                obpay["result_number"] = ob.value
                obpay["result_type"] = ObservationResultType.Number
            elif isinstance(ob.value, str):
                obpay["result_string"] = ob.value
                obpay["result_type"] = ObservationResultType.String
            elif isinstance(ob.value, bool):
                obpay["result_boolean"] = ob.value  # noqa
                obpay["result_type"] = ObservationResultType.Bool
            elif isinstance(ob.value, dict):
                obpay["result_json"] = json.dumps(ob.value)
                obpay["result_type"] = ObservationResultType.Json
            else:
                journal.warning(
                    f"Data of type {type(ob.value).__name__} is "
                    f"not supported. Failing Observation: {ob}",
                    thing_uuid,
                )
                continue
            result.append(obpay)

        return result


class CampbellCr6Parser(MqttDataParser):
    # the basic data massage looked like this
    # {
    #     "type": "Feature",
    #     "geometry": {"type": "Point", "coordinates": [null, null, null]},
    #     "properties": {
    #         "loggerID": "CR6_18341",
    #         "observationNames": ["Batt_volt_Min", "PTemp"],
    #         "observations": {"2022-05-24T08:53:00Z": [11.9, 26.91]}
    #     }
    # }

    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        properties = rawdata.get("properties")
        if properties is None:
            return []

        out = []
        for timestamp, values in properties["observations"].items():
            for i, (key, value) in enumerate(
                zip(properties["observationNames"], values)
            ):
                out.append(
                    Observation(
                        timestamp=timestamp,
                        value=value,
                        position=i,
                        origin=origin,
                        header=key,
                    )
                )
        return out


class YdocMl417Parser(MqttDataParser):
    # mqtt_ingest/test-logger-pb/test/data/jsn
    # {
    # "device":
    #   {"sn":99073020,"name":"UFZ","v":"4.2B5","imei":353081090730204,"sim":89490200001536167920},
    # "channels":[
    #   {"code":"SB","name":"Signal","unit":"bars"},
    #   {"code":"MINVi","name":"Min voltage","unit":"V"},
    #   {"code":"AVGVi","name":"Average voltage","unit":"V"},
    #   {"code":"AVGCi","name":"Average current","unit":"mA"},
    #   {"code":"P1*","name":"pr2_1_10","unit":"m3/m3"},
    #   {"code":"P2","name":"pr2_1_20","unit":"m3/m3"},
    #   {"code":"P3","name":"pr2_1_30","unit":"m3/m3"},
    #   {"code":"P4","name":"pr2_1_40","unit":"m3/m3"},
    #   {}],
    # "data":[
    #   {"$ts":230116110002,"$msg":"WDT;pr2_1"},    <== we ignore that (*)
    #   {"$ts":230116110002,"MINVi":3.74,"AVGVi":3.94,"AVGCi":116,"P1*":"0*T","P2":"0*T","P3":"0*T","P4":"0*T"},
    #   {}]}

    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        if "data/jsn" not in origin:
            return []

        # data = payload['data'][1]
        ret = []
        for data in rawdata["data"]:
            try:
                ts = datetime.strptime(str(data["$ts"]), "%y%m%d%H%M%S")
                ob0 = Observation(ts, data["MINVi"], origin, 0, header="MINVi")
                ob1 = Observation(ts, data["AVGVi"], origin, 1, header="AVGCi")
                ob2 = Observation(ts, data["AVGCi"], origin, 2, header="AVGCi")
                ob3 = Observation(ts, data["P1*"], origin, 3, header="P1*")
                ob4 = Observation(ts, data["P2"], origin, 4, header="P2")
                ob5 = Observation(ts, data["P3"], origin, 5, header="P3")
                ob6 = Observation(ts, data["P4"], origin, 6, header="P4")
                ret.extend([ob0, ob1, ob2, ob3, ob4, ob5, ob6])
            except KeyError:
                # we ignore data that not have all keys
                # see also the example above the function at (*)
                pass
        return ret


class BrightskyDwdApiParser(MqttDataParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        weather = rawdata["weather"]
        timestamp = weather.pop("timestamp")
        source = rawdata["sources"][0]
        out = []
        for prop, value in weather.items():
            try:
                out.append(
                    Observation(
                        timestamp=timestamp,
                        value=value,
                        position=prop,
                        origin=origin,
                        header=source,
                    )
                )
            except ValueError:  # value is NaN or None
                continue

        return out


class SineDummyParser(MqttDataParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        timestamp = datetime.now()
        return [
            Observation(
                timestamp=timestamp,
                value=rawdata["sine"],
                position=0,
                origin=origin,
                header="sine",
            ),
            Observation(
                timestamp=timestamp,
                value=rawdata["cosine"],
                position=1,
                origin=origin,
                header="cosine",
            ),
        ]


def get_parser(parser_type, settings) -> FileParser | MqttDataParser:
    types = {
        "csvparser": CsvParser,
        "campbell_cr6": CampbellCr6Parser,
        "brightsky_dwd_api": BrightskyDwdApiParser,
        "ydoc_ml417": YdocMl417Parser,
        "sine_dummy": SineDummyParser,
    }
    klass = types.get(parser_type)
    if klass is None:
        raise NotImplementedError(f"parser {parser_type!r} not known")

    if issubclass(klass, FileParser):
        if not settings:
            settings = {}
        default_settings = {
            "comment": "#",
            "decimal": ".",
            "na_values": None,
            "encoding": "utf-8",
            "engine": "python",
            "on_bad_lines": "warn",
            "header": None,
        }

        kwargs = settings.pop("pandas_read_csv") or {}
        settings = {**default_settings, **kwargs, **settings}
        return klass(settings)
    return klass()
