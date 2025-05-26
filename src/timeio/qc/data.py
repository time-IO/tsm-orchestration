#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime
import logging
import typing
import warnings
from typing import Any, Hashable, Literal, cast

import pandas as pd
from dns.opcode import QUERY
from psycopg import Connection, sql
from timeio.typehints import DbRowT, JsonObjectT

try:
    from psycopg_pool import ConnectionPool
except ImportError:
    ConnectionPool = typing.TypeVar("ConnectionPool")  # noqa

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
TimestampT = typing.Union[datetime.datetime.timestamp, pd.Timestamp]



class Datastream:
    QUERY = """
    select "RESULT_TIME","RESULT_TYPE","RESULT_NUMBER","RESULT_STRING","RESULT_JSON",
        "RESULT_BOOLEAN","RESULT_QUALITY",l.datastream_id as raw_datastream_id
    from {schema}."OBSERVATIONS" o 
    join public.sms_datastream_link l on o."DATASTREAM_ID" = l.device_property_id
    where o."DATASTREAM_ID" = %s
      and o."RESULT_TIME" >= %s
      and o."RESULT_TIME" <= %s
    order by o."RESULT_TIME" desc
    limit %s """

    def __init__(
        self,

        stream_id: int,
        start_date: TimestampT | None,
        end_date: TimestampT | None,
    ):
        if start_date is None:
            start_date = "-Infinity"
        if end_date is None:
            end_date = "Infinity"
        self.stream_id = stream_id
        self.start_date = start_date
        self.end_date = end_date
        self.schema = schema

    def fetch(self) -> list[DbRowT] | None:

        # (start_date - window) <= start_date <= data <= end_date
        # [===context window===]+[===============data============]

        # Mind that o."DATASTREAM_ID" is the STA datastream id
        query = sql.SQL(self.QUERY).format(schema=sql.Identifier(self.schema))

        # Fetch data by dates including context window, iff it was defined
        # as a timedelta. None as limit, becomes SQL:'LIMIT NULL' which is
        # equivalent to 'LIMIT ALL'.
        params = [sta_stream_id, start_date, end_date, None]
        data = self.conn.execute(query, params).fetchall()
        if not data:  # If we have no data we also need no context data
            return None

        # Fetch data from context window, iff it was passed as a number,
        # which means number of observations before the actual data.
        context = []
        if isinstance(window, int) and window > 0:
            params = [sta_stream_id, "-Infinity", start_date, window]
            context = self.conn.execute(query, params).fetchall()
            # If the exact start_date is present in the data, the usage
            # of `>=` and `<=` will result in a duplicate row.
            if len(context) > 0 and context[0][0] == data[-1][0]:
                context = context[1:]

        # In the query we ordered descending (newest first) to correctly
        # use the limit keyword, but for python/pandas etc. we want to
        # return an ascending (oldest first) data set.
        return context[::-1] + data[::-1]
