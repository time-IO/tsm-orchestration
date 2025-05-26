#!/usr/bin/env python3
import datetime

import pandas as pd
import psycopg
from psycopg import sql
from psycopg.generators import fetch

from timeio.qc.typeshints import TimestampT, WindowT


class Datastream:

    def __init__(
        self,
        thing_id: str,
        stream_id: str,
        name: str,
        db_conn: psycopg.Connection,
        schema: str,
    ):
        self.thing_id = thing_id
        self.stream_id = stream_id
        self.name = name
        self.schema = schema
        self._conn = db_conn
        self._data = pd.Series(dtype="object", index=pd.DatetimeIndex())

    def _fetch(
        self, start: TimestampT, end: TimestampT, limit: int | None = None
    ) -> pd.Series:
        """
        Fetch data between two datetimes from the database.
        Returns a pandas Series with datetime index.
        """

        query = sql.SQL(
            """
                select
                    "RESULT_TIME",
                    "RESULT_TYPE",
                    "RESULT_NUMBER",
                    "RESULT_STRING",
                    "RESULT_JSON",
                    "RESULT_BOOLEAN",
                    "RESULT_QUALITY",
                    l.datastream_id as raw_datastream_id 
                from "OBSERVATIONS" o 
                join public.sms_datastream_link l 
                on o."DATASTREAM_ID" = l.device_property_id 
                where o."DATASTREAM_ID" = %s 
                and o."RESULT_TIME" >= %s 
                and o."RESULT_TIME" <= %s 
                order by o."RESULT_TIME" desc 
                limit %s 
            """
        )
        with self._conn.cursor() as cur:
            cur.execute("set searchpath to %s", [self.schema])
            cur.execute(query, (self.stream_id, start, end))
            rows = cur.fetchall()

        if not rows:
            return pd.Series(dtype="object", index=pd.DatetimeIndex())

        timestamps, values = zip(*rows)
        return pd.Series(data=values, index=pd.to_datetime(timestamps))

    def get_unflagged_range(self) -> tuple[TimestampT, TimestampT] | tuple[None, None]:
        """Returns (earliest, latest) timestamp of unflagged data."""

        # Mind that o."DATASTREAM_ID" is the STA datastream id
        part = """ \
               select o."RESULT_TIME" from {schema}."OBSERVATIONS" o
               where o."DATASTREAM_ID" = %s and
                   (o."RESULT_QUALITY" is null or o."RESULT_QUALITY" = 'null'::jsonb)
               order by "RESULT_TIME" {order} limit 1 \
               """
        newest = sql.SQL(part).format(
            schema=sql.Identifier(self.schema), order=sql.SQL("desc")
        )
        oldest = sql.SQL(part).format(
            schema=sql.Identifier(self.schema), order=sql.SQL("asc")
        )
        query = sql.SQL('({}) UNION ALL ({}) ORDER BY "RESULT_TIME"').format(
            oldest, newest
        )
        r = self._conn.execute(query, [self.stream_id, self.stream_id]).fetchall()
        if not r:
            return None, None
        return r[0][0], r[1][0]

    def get(self, start: TimestampT, end: TimestampT, context_window=None) -> pd.Series:
        """
        Return data between start and end.
        Fetch missing data from DB if needed.
        """
        if self._data.empty:
            self._data = self._fetch(start, end)
        else:
            missing_start = start < self._data.index.min()
            missing_end = end > self._data.index.max()

            if missing_start:
                fetched = self._fetch(start, self._data.index.min())
                self._data = fetched.combine_first(self._data)

            if missing_end:
                fetched = self._fetch(self._data.index.max(), end)
                self._data = self._data.combine_first(fetched)

        chunk = self._data.loc[start:end]
        if chunk.empty or context_window is None:
            return chunk

        context_start = self._fetch_context(start, context_window)
        return self._data.loc[context_start:end]

    def _fetch_context(self, start: TimestampT, window: WindowT) -> datetime.datetime:
        """
        Fetches the context window and
        returns the timestamp of the first value.
        """
        if isinstance(window, pd.Timedelta):
            end = start
            start -= window
            if start < self._data.index.min():
                fetched = self._fetch(start, end)
                self._data = fetched.combine_first(self._data)
            return start

        assert isinstance(window, int)
        pre_chunk = self._data.loc[:start]
        # We must account that pandas is inclusive, but the
        # context-window are the number of data pints BEFORE
        # the first data to process. The query to fetch the
        # data is also inclusive, so we have an overlap of
        # one observation, but that's ok, I guess.
        window += 1
        missing = window - len(pre_chunk)
        if missing > 1:
            fetched = self._fetch("-Infinity", start, limit=missing)
            self._data = fetched.combine_first(self._data)
        return self._data.loc[:start].index[-window]

    def __repr__(self):
        return (
            f"Datastream({self.thing_id}, {self.stream_id}, {self.name}, "
            f"cached={len(self._data)} rows)"
        )
