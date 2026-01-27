#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import typing

import pandas as pd

import psycopg
from psycopg import sql

from timeio.cast import rm_tz
from timeio.qc.qctest import QcTest, StreamInfo

if typing.TYPE_CHECKING:
    from timeio import feta
    from timeio.qc.typeshints import TimestampT

__all__ = ["get_functions_to_execute", "get_qc_functions"]

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
                *map(lambda row: (row[0], (row[row[1] + 2], row[6], row[7])), cur)
            )
            index = pd.to_datetime(timestamps, utc=True)
            # To avoid errors from mixing TZ aware and TZ unaware objects.
            # We handle everything in UTC without TZ.
            index = rm_tz(index)

        out = pd.DataFrame(
            data,
            index=index,
            columns=["data", "quality", "stream_id"],
        )
        out["data"] = out["data"].astype(float)
        out["quality"] = out["quality"].astype(object)
        out["stream_id"] = out["stream_id"].astype(int)
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
        limit: int | None = None
    ) -> pd.DataFrame:
        query = f"""
        SELECT
            "RESULT_TIME",
            "RESULT_TYPE",
            "RESULT_NUMBER",
            "RESULT_STRING",
            "RESULT_JSON",
            "RESULT_BOOLEAN",
            "RESULT_QUALITY",
            l.datastream_id
        FROM {schema}."OBSERVATIONS" o
          JOIN public.sms_datastream_link l ON o."DATASTREAM_ID" = l.device_property_id
        WHERE o."DATASTREAM_ID" = %s
          AND o."RESULT_TIME" >= %s
          AND o."RESULT_TIME" <= %s
        ORDER BY o."RESULT_TIME" DESC
            LIMIT %s
        """
        cur.execute(sql.SQL(query), (datastream_id, start_date, end_date, limit))
        return to_frame(cur)

    if start_date in [None, pd.NaT]:
        start_date = "-Infinity"

    if end_date in [None, pd.NaT]:
        end_date = "Infinity"

    out = {}

    with db_conn.cursor() as cur:
        # for stream in set(streams):
        for stream in streams:
            schema, datastream_id = query_datastream_id(cur, stream.stream_id)
            out[stream.value] = query_datastream(
                cur, schema, datastream_id, start_date, end_date, limit
            )

    return out


def get_functions(conf: feta.QAQC) -> list[QcTest]:
    """
    Convert between the database/feta layer and business logic objects
    """

    def get_func_fields(test: feta.QAQCTest):
        out = []
        for stream in test.streams or []:
            if stream["arg_name"] == "field":
                out.append(
                    StreamInfo(
                        stream["arg_name"],
                        stream["alias"],
                        stream["sta_thing_id"],
                        stream["sta_stream_id"],
                    )
                )
        return out

    def get_func_targets(test: feta.QAQCTest):
        out = []
        for stream in test.streams or []:
            if stream["arg_name"] == "target":
                out.append(
                    StreamInfo(
                        stream["arg_name"],
                        stream["alias"],
                        stream["sta_thing_id"],
                        stream["sta_stream_id"],
                    )
                )
        return out

    out = []
    for i, func in enumerate(conf.get_tests(), start=1):
        try:
            qctest = QcTest(
                name=func.name,
                func_name=func.function,
                fields=get_func_fields(func),
                targets=get_func_targets(func),
                params=func.args,
                context_window=conf.context_window,
            )
        except Exception as e:
            e.add_note(f"Qc test {i} ({func})")
            e.add_note(f"Config {conf}")
            raise e
        out.append(qctest)

    return out


def filter_thing_funcs(funcs: list[QcTest], thing_id: int) -> list[QcTest]:
    out = []
    for func in funcs:
        thing_ids = set(int(f.thing_id) for f in func.fields)
        if thing_id in thing_ids:
            out.append(func)
    return out


def filter_funcs_to_execute(all_funcs: list[QcTest], selected_funcs: list[QcTest]):

    to_check = []
    for func in selected_funcs:
        targets = set(t.value for t in func.targets)
        for target in targets:
            to_check.append(target)

    # build up the function look up table
    lut = {}
    for func in all_funcs:
        fields = set(f.value for f in func.fields)
        for field in fields:
            lut[field] = func

    seen = set(selected_funcs)

    # NOTE:
    # we explicitly allow cyclic dependencies, they are resolved in definition order
    # in a setting like
    # func1(field=x, target=y)
    # func2(field=y, target=x)
    # we allow func1 to write y and func2 to overwrite x
    for target in to_check:
        if target in lut:
            func = lut[target]
            to_check.append(func)
            if func not in seen:
                selected_funcs.append(func)

    return selected_funcs


def get_functions_to_execute(funcs: list[QcTest], thing_id) -> list[QcTest]:

    thing_funcs = filter_thing_funcs(funcs, thing_id)
    funcs_to_process = filter_funcs_to_execute(funcs, thing_funcs)
    return funcs_to_process
