#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import copy
import logging
import typing
import json
from collections import defaultdict

import pandas as pd

import psycopg
from psycopg import sql

from timeio.cast import rm_tz
from timeio.common import ObservationResultType, get_result_field_name
from timeio.databases import DBapi

if typing.TYPE_CHECKING:
    from timeio.qc.typehints import TimestampT
    from timeio.qc.saqc import SaQCWrapper


logger = logging.getLogger("run-quality-control")


class StreamInfo:
    """Dataclass that stores a stream parameter for a quality test function
    stream_id and thing_id are definied as SMS entities with
    - stream_id -> device_propert_id
    - thing_id  -> configuration_id
    """

    def __init__(
        self,
        key: typing.Literal["field", "target"],
        alias: str,
        sta_thing_id: int,
        sta_stream_id: int | None,
        mutable: bool,
        position: str,
        schema: str,
        datastream_id: int | None,
        thing_uuid: str,
        context_window: pd.Timedelta,
    ):
        # TODO: improve attribute names
        self.key = key
        self.alias: str = alias
        self.sms_configuration_id = sta_thing_id
        self.sta_stream_id = sta_stream_id
        self.datastream_name: str = alias
        self.db_schema = schema
        self.db_stream_id = datastream_id
        self.thing_uuid = thing_uuid
        self.position = position
        self.is_mutable = mutable
        self.context_window = context_window

    def to_target(self):
        out = copy.deepcopy(self)
        out.key = "target"
        return out

    def __eq__(self, other):
        if not isinstance(other, StreamInfo):
            return NotImplemented
        return (
            self.sms_configuration_id == other.sms_configuration_id
            and self.sta_stream_id == other.sta_stream_id
        )

    def __hash__(self):
        return hash((self.alias, self.sms_configuration_id, self.sta_stream_id))

    def __repr__(self):
        klass = self.__class__.__name__
        return f"{klass}({self.key}, {self.alias})"


def get_result_type(data: pd.Series):
    # NOTE:
    # - That seems to be a lot of effort...
    # - I guess we do the same things at various
    #   places throughout the codebase
    if pd.api.types.is_numeric_dtype(data):
        return ObservationResultType.Number
    elif pd.api.types.is_string_dtype(data):
        return ObservationResultType.String
    elif pd.api.types.is_bool_dtype(data):
        return ObservationResultType.Bool
    elif pd.api.types.is_object_dtype(data):
        return ObservationResultType.Json
    else:
        raise ValueError(f"Data of type {data.dtype} is not supported.")


def query_datastream(
    cur: psycopg.Cursor,
    schema: str,
    datastream_id: int,
    start_date: TimestampT,
    end_date: TimestampT,
) -> pd.DataFrame:

    def to_frame(cur: psycopg.Cursor) -> pd.DataFrame:
        data = None
        index = pd.DatetimeIndex([])
        if cur.rowcount > 0:
            timestamps, data = zip(
                *map(lambda row: (row[0], (row[row[1] + 2], row[6])), cur)
            )
            index = pd.to_datetime(timestamps, utc=True)
            # To avoid errors from mixing TZ aware and TZ unaware objects.
            # We handle everything in UTC without TZ.
            index = rm_tz(index)

        out = pd.DataFrame(
            data,
            index=index,
            columns=["data", "quality"],
        )
        out["data"] = out["data"].astype(float)
        out["quality"] = out["quality"].astype(object)
        return out

    query = f"""
    SELECT
        "RESULT_TIME",
        "RESULT_TYPE",
        "RESULT_NUMBER",
        "RESULT_STRING",
        "RESULT_JSON",
        "RESULT_BOOLEAN",
        "RESULT_QUALITY"
    FROM {schema}."OBSERVATIONS" o
      JOIN public.sms_datastream_link l ON o."DATASTREAM_ID" = l.device_property_id
    WHERE o."DATASTREAM_ID" = %s
      AND o."RESULT_TIME" >= %s
      AND o."RESULT_TIME" <= %s
    ORDER BY o."RESULT_TIME" DESC
    """
    cur.execute(sql.SQL(query), (datastream_id, start_date, end_date))
    df = to_frame(cur)
    return df


def write_qc_data(dbapi: DBapi, qc: SaQCWrapper):

    def convert_df(stream: StreamInfo, df: pd.DataFrame):
        # trim context window away
        df = df.loc[df.index[0] + stream.context_window:]

        df["result_time"] = df.index.strftime("%Y-%m-%dT%H:%M:%S")
        df["result_type"] = rt = get_result_type(df["data"])
        df["datastream_id"] = stream.db_stream_id
        df["datastream_pos"] = stream.datastream_name
        columns_map = {
            "quality": "result_quality",
            "data": get_result_field_name(rt, errors="raise"),
        }
        df = df.rename(columns=columns_map)
        df["result_quality"] = df["result_quality"].map(json.dumps)
        return df

    def upload_full_streams(streams: dict[str, list]):

        for thing_uuid, dfs in streams.items():
            df = pd.concat(dfs)

            # datastreams
            stream_names = (
                df.loc[df["datastream_id"].isnull(), "datastream_pos"]
                .drop_duplicates()
                .tolist()
            )
            if stream_names:
                # create newly generated datastreams
                datastreams = dbapi.insert_datastreams(
                    thing_uuid=thing_uuid,
                    datastreams=[{"datastream_pos": n} for n in stream_names],
                    mutable=True,
                )
                # add ids
                df = (
                    df.merge(
                        pd.DataFrame(datastreams).rename(
                            columns={"id": "datastream_id"}
                        ),
                        left_on="datastream_pos",
                        right_on="position",
                        suffixes=("_x", "_y"),
                    )
                    .drop(columns="datastream_id_x")
                    .rename(columns={"datastream_id_y": "datastream_id"})
                )

            # observations
            observations = df.drop(columns="result_quality").to_dict(orient="records")
            dbapi.upsert_observations(thing_uuid=thing_uuid, observations=observations)

            # qaqc
            labels = df[["result_time", "result_quality", "datastream_id"]]
            dbapi.upsert_qc_labels(
                thing_uuid=thing_uuid, qc_labels=labels.to_dict(orient="records")
            )

    def upload_quality(streams: dict[str, list]):
        for thing_uuid, dfs in streams.items():
            df = pd.concat(dfs)
            labels = df[["result_time", "result_quality", "datastream_id"]]
            labels["result_quality"] = labels["result_quality"]

            dbapi.upsert_qc_labels(
                thing_uuid=thing_uuid, qc_labels=labels.to_dict(orient="records")
            )

    full_streams = defaultdict(list)
    qc_streams = defaultdict(list)
    for stream, df in qc.data.items():
        # TODO: simplify the outer case selection away, if possible
        if df.empty:
            continue
        converted = convert_df(stream, df)

        if stream.sta_stream_id is None:
            # we have a newly created datastream -> simply upload
            full_streams[stream.thing_uuid].append(converted)
        elif qc.data_is_modified(stream):
            if not stream.is_mutable:
                raise ValueError(f"changes to immutable datatstream {stream} detected")
            if qc.index_is_modified(stream):
                dbapi.delete_observations(
                    stream.thing_uuid,
                    stream.datastream_name,
                    start_date=converted.index[0],
                    end_date=converted.index[-1],
                )
                full_streams[stream.thing_uuid].append(converted)
        else:
            qc_streams[stream.thing_uuid].append(converted)

    upload_full_streams(full_streams)
    upload_quality(qc_streams)


def read_stream_data(
    db_conn: psycopg.Connection,
    streams: list[StreamInfo] | set[StreamInfo],
    start_date: TimestampT | None = None,
    end_date: TimestampT | None = None,
) -> dict[StreamInfo, pd.DataFrame]:

    if start_date is None or start_date == pd.NaT:
        start_date = pd.Timestamp("1700-01-01")

    if end_date is None or end_date == pd.NaT:
        end_date = pd.Timestamp("3000-12-11")

    out = {}
    with db_conn.cursor() as cur:
        # for stream in set(streams):
        for stream in streams:
            if stream.db_stream_id:
                df = query_datastream(
                    cur,
                    stream.db_schema,
                    stream.db_stream_id,
                    start_date - stream.context_window,
                    end_date,
                )
                out[stream] = df

    return out
