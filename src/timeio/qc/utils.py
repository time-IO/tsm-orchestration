#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import typing

import pandas as pd

import psycopg
from psycopg import sql

from timeio.cast import rm_tz
from timeio.qc.qcfunction import StreamInfo

if typing.TYPE_CHECKING:
    from timeio.qc.typehints import TimestampT


logger = logging.getLogger("run-quality-control")


def load_data(
    db_conn: psycopg.Connection,
    streams: list[StreamInfo],
    start_date: TimestampT | str | None = None,
    end_date: TimestampT | str | None = None,
    limit: int | None = None,
) -> dict[str, pd.DataFrame]:

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

    def query_datastream_id(cur: psycopg.Cursor, sta_id: int) -> tuple[str, int]:
        query = """
        SELECT
            datasource_id as schema,
            datastream_id
        FROM public.sms_datastream_link
        WHERE device_property_id = %s
        """
        cur.execute(sql.SQL(query), (sta_id,))
        result = cur.fetchone()
        if not result:
            raise ValueError(f"STA Datastream ID '{sta_id}' does not exist")
        return result

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
        df.attrs["datastream_id"] = datastream_id
        # TODO: fill to take care of the context window
        df.attrs["start_pos"] = None
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
                # TODO: shrink data range
                pass
            schema, datastream_id = query_datastream_id(cur, stream.stream_id)
            out[stream.name] = query_datastream(
                cur, schema, datastream_id, start_date, end_date, limit
            )

    return out
