#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import typing
from collections import defaultdict

import requests
import pandas as pd

import psycopg
from psycopg import sql

from timeio.cast import rm_tz
from timeio.qc.qcfunction import StreamInfo
from timeio.qc.saqc import SaQCWrapper
from timeio.common import ObservationResultType, get_result_field_name

if typing.TYPE_CHECKING:
    from timeio.qc.typehints import TimestampT


logger = logging.getLogger("run-quality-control")


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


def query_datastream_info(
    cur: psycopg.Cursor, sta_id: int
) -> tuple[str, str, int, str]:
    cur.execute(
        sql.SQL("""
        SELECT
            datasource_id as schema,
            thing_id as thing_uuid,
            datastream_id
        FROM public.sms_datastream_link
          WHERE device_property_id = %s
        """),
        (sta_id,),
    )
    result = cur.fetchone()
    if result is None:
        raise ValueError(f"STA Datastream ID '{sta_id}' does not exist")
    schema, thing_id, datastream_id = result

    cur.execute(
        sql.SQL(f"""
    SELECT position FROM {schema}.datastream where id = %s
    """),
        (datastream_id,),
    )
    result = cur.fetchone()
    if result is None:
        raise ValueError(f"Datastream ID '{datastream_id}' does not exist")
    return schema, thing_id, datastream_id, result[0]


def write_data(conn: psycopg.Connection, qc: SaQCWrapper, dbapi_url: str):

    # TODO: take care of the context window

    def get_thing_uuid(cur: psycopg.Cursor, configuration_id: int) -> str:
        query = """
        SELECT DISTINCT
            thing_id
        FROM
          sms_device_mount_action m
          JOIN sms_configuration c on c.id = m.configuration_id
          JOIN sms_datastream_link l on l.device_mount_action_id = m.id
        WHERE configuration_id = %s
        """
        cur.execute(sql.SQL(query), (configuration_id,))

        result = cur.fetchone()
        assert len(result) == 1
        return str(result[0])

    def convert_df(stream: StreamInfo, df: pd.DataFrame):
        df["result_time"] = df.index
        df["result_type"] = rt = get_result_type(df["data"])
        df["datastream_id"] = stream.db_stream_id
        df["datastream_pos"] = stream.datastream_name
        columns_map = {
            "quality": "result_quality",
            "data": get_result_field_name(rt, errors="raise"),
        }
        df = df.rename(columns=columns_map)
        # df = df.to_json(orient="records", date_format="iso")
        return df

    def upload_product_streams(dbapi_url: str, streams: dict[str, list]):

        for thing_uuid, dfs in streams.items():
            # upload data
            df = pd.concat(dfs)
            data = df.drop(columns="result_quality").to_json(orient="records", date_format="iso")

            # r = requests.post(
            #     f"{dbapi_url}/qaqc/upsert/{thing_uuid}",
            #     data=f'{{"qaqc_labels":{out}}}',
            #     headers={"Content-type": "application/json"},
            # )
            r = requests.post(
                f"{dbapi_url}/observations/upsert/{thing_uuid}",
                data=f'{{"observations":{data}}}',
                headers={"Content-type": "application/json"},
            )
            r.raise_for_status()
            # TODO: upload qaqc

    product_streams = defaultdict(list)
    qc_streams = defaultdict(list)
    with conn.cursor() as cur:
        for stream, df in qc.data.items():
            converted = convert_df(stream, df)
            if stream.sta_stream_id is None:
                # we have a newly created datastream -> simply upload
                thing_uuid = get_thing_uuid(cur, stream.sta_thing_id)
                product_streams[thing_uuid].append(
                    converted.drop(columns=["datastream_id"])
                )
            else:
                # we have a pre-existing datastream
                # check whether the data was modified
                if qc.data_is_modified(stream):
                    # TODO when DB-API changes are merged:
                    # - check, if datastream is mutable
                    # - delete datastream data from the database if necessary
                    pass
                # NOTE:
                # unsure, if we might see othe data types as well
                # I guess not, as SaQC is expecting numerical data
                qc_streams[stream.db_schema].append(
                    converted.drop(columns=["result_number"])
                )

    upload_product_streams(dbapi_url, product_streams)


def load_data(
    db_conn: psycopg.Connection,
    streams: list[StreamInfo],
    start_date: TimestampT | str | None = None,
    end_date: TimestampT | str | None = None,
    limit: int | None = None,
) -> dict[StreamInfo, pd.DataFrame]:

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

    def query_datastream(
        cur: psycopg.Cursor,
        schema: str,
        datastream_id: int,
        start_date: TimestampT | str,
        end_date: TimestampT | str,
        limit: int | None = None,
    ) -> pd.DataFrame:
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
            LIMIT %s
        """
        cur.execute(sql.SQL(query), (datastream_id, start_date, end_date, limit))
        df = to_frame(cur)
        return df

    if start_date in [None, pd.NaT]:
        start_date = "-Infinity"

    if end_date in [None, pd.NaT]:
        end_date = "Infinity"

    out = {}

    with db_conn.cursor() as cur:
        # for stream in set(streams):
        for stream in streams:
            if stream.is_immutable:
                # TODO: extend data range to take context window into account
                pass
            schema, _, datastream_id, datastream_pos = query_datastream_info(
                cur, stream.sta_stream_id
            )
            df = query_datastream(
                cur, schema, datastream_id, start_date, end_date, limit
            )
            stream.db_schema = schema
            stream.db_stream_id = datastream_id
            stream.datastream_name = datastream_pos
            out[stream] = df

    return out
