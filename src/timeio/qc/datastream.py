#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import psycopg
from psycopg import sql

from timeio.qc.typeshints import TimestampT, WindowT

__all__ = ["Datastream"]

""" 
This module provides a convenient abstraction for retrieving and 
storing datastreams from/to the users observation database.
"""

QUALITY_COLUMNS = ["quality", "measure", "userLabel"]


def _extract(row) -> tuple[datetime, tuple[Any, int, int]]:
    """
    This mainly extracts the data from the number-, string-,
    json-, or the boolean-columns. The info, which column holds
    the data is numerically encoded in the result_type column.
    We return a nested tuple:
        (RESULT_TIME, (DATA, QUALITY, RAW_STREAM_ID))
    """
    return row[0], (row[row[1]], row[6], row[7])


class DatastreamSTA:

    _columns = ["data", "quality", "raw_stream_id"]

    def __init__(
        self,
        thing_id: int,
        stream_id: int,
        name: str,
        db_conn: psycopg.Connection,
        schema: str,
    ):
        # Mind that thing_id and stream_id are
        # the STA thing id and STA datastream id.
        self.thing_id = thing_id
        self.stream_id = stream_id
        self.name = name
        self.schema = schema

        self._conn = db_conn
        self._data = pd.DataFrame([], pd.DatetimeIndex([]), self._columns, "object")
        self._unflagged: tuple[datetime, datetime] | None = None

    def _append(self, new_data, overwrite=False):
        """Appends given dataframe to the internal _data."""
        data = pd.concat([self._data, new_data])
        keep = "last" if overwrite else "first"
        self._data = data[~data.index.duplicated(keep=keep)].sort_index()

    def _fetch(
        self,
        date_start: TimestampT,
        date_end: TimestampT | None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Fetch data between two datetimes from the database.
        Returns a pandas Series with datetime index.
        """
        # Note that, limit=None translates to 'LIMIT NULL'
        # in postgres which is equivalent to 'LIMIT ALL',
        # which effectively disables the limit for the query.
        query = sql.SQL(
            """
                select "RESULT_TIME", "RESULT_TYPE", "RESULT_NUMBER", "RESULT_STRING",
                    "RESULT_JSON", "RESULT_BOOLEAN", "RESULT_QUALITY",  l.datastream_id 
                from "OBSERVATIONS" o 
                join public.sms_datastream_link l on o."DATASTREAM_ID" = l.device_property_id 
                where o."DATASTREAM_ID" = %s 
                  and o."RESULT_TIME" >= %s 
                  and o."RESULT_TIME" <= %s 
                order by o."RESULT_TIME" desc 
                limit %s 
            """
        )

        if date_end is None:
            date_end = "Infinity"

        with self._conn.cursor() as cur:
            cur.execute("set searchpath to %s", [self.schema])
            cur.execute(query, (self.stream_id, date_start, date_end, limit))

            data = None
            index = pd.DatetimeIndex([])
            if cur.rowcount > 0:
                timestamps, data = zip(*map(_extract, cur))
                index = pd.to_datetime(timestamps)

        return pd.DataFrame(data, columns=self._columns, index=index)

    def _fetch_context(self, date_start: TimestampT, window: WindowT) -> pd.Timestamp:
        """Fetches the context window and returns its first timestamp."""
        data_start = self._data.index.min()

        if isinstance(window, pd.Timedelta):
            new_start = date_start - window
            if new_start < data_start:
                fetched = self._fetch(new_start, data_start)
                self._append(fetched)
            return new_start

        assert isinstance(window, int)
        # We must account that pandas is inclusive and the
        # context-window is the number of data points BEFORE
        # the first data to process. The query to fetch the
        # data also includes the start and end dates. With
        # this we always have an overlap of exactly one
        # observation.
        window += 1
        pre_chunk = self._data.loc[:date_start]
        missing = window - len(pre_chunk)
        if missing > 1:
            fetched = self._fetch("-Infinity", data_start, limit=missing)
            self._append(fetched)
        return self._data.loc[:date_start].index[-window]

    def get_unprocessed_range(
        self,
    ) -> tuple[TimestampT, TimestampT] | tuple[None, None]:
        """Returns (earliest, latest) timestamp of data that was never seen by QC."""
        query = """ 
           select o."RESULT_TIME" from "OBSERVATIONS" o
           where o."DATASTREAM_ID" = %s 
             and (o."RESULT_QUALITY" is null or o."RESULT_QUALITY" = 'null'::jsonb)
           order by "RESULT_TIME" {order} 
           limit 1
        """

        if self._unflagged is None:
            q1 = sql.SQL(query).format(order=sql.SQL("desc"))
            q2 = sql.SQL(query).format(order=sql.SQL("asc"))

            with self._conn.cursor() as cur:
                cur.execute("set searchpath to %s", [self.schema])
                newest = cur.execute(q1, [self.stream_id]).fetchone() or [None]
                oldest = cur.execute(q2, [self.stream_id]).fetchone() or [None]

            self._unflagged = newest[0], oldest[0]

        return self._unflagged

    def get_data(
        self,
        date_start: TimestampT | None,
        date_end: TimestampT | None,
        context_window: WindowT,
    ) -> pd.Series:
        """
        Return data between date_start and date_end.
        Fetch missing data from DB if needed.
        """
        if date_start is None:
            return pd.Series(index=pd.DatetimeIndex([]))

        if self._data.empty:
            self._data = self._fetch(date_start, date_end)
        else:
            missing_start = date_start < self._data.index.min()
            missing_end = (date_end or pd.NaT) > self._data.index.max()

            if missing_start:
                fetched = self._fetch(date_start, self._data.index.min())
                self._append(fetched)

            if missing_end:
                fetched = self._fetch(self._data.index.max(), date_end)
                self._append(fetched)

        chunk = self._data.loc[date_start:date_end]
        if chunk.empty or context_window is None:
            return chunk

        context_start = self._fetch_context(date_start, context_window)
        return self._data.loc[context_start:date_end, "data"]

    def get_quality_labels(
        self,
        date_start: TimestampT | None,
        date_end: TimestampT | None,
        context_window: WindowT,
    ) -> pd.DataFrame:
        if date_start is None:
            pass
        # We might need to fetch the data first ...
        self.get_data(date_start, date_end, context_window)
        return self._data.loc[date_start:date_end, QUALITY_COLUMNS]

    def __repr__(self):
        klass = self.__class__.__name__
        return (
            f"{klass}({self.thing_id}, {self.stream_id}, {self.name}, "
            f"cached={len(self._data.index)} rows)"
        )

    def update_quality_labels(self, labels: pd.DataFrame) -> None:
        """
        This acts like uploading data to the DB, but instead of
        really uploading the data, the data is stored within the
        stream abstraction (this class).
        """
        unknown = labels.index.difference(self._data.index)
        if not unknown.empty:
            pass  # todo warn about unknown labels
        index = labels.index.intersection(self._data.index)
        columns = labels.columns.intersection(QUALITY_COLUMNS)
        self._data.loc[index, columns] = labels[columns]

    def upload(self, overwrite=True):
        """Update locally stored quality labels to the DB"""
        pass  # todo: Upload quality labels


Datastream = DatastreamSTA


class ProductStream(Datastream):

    def __init__(
        self,
        thing_id: int,
        stream_id: int | None,
        name: str,
        db_conn: psycopg.Connection,
        schema: str,
    ):
        super().__init__(thing_id, stream_id, name, db_conn, schema)
        assert stream_id is None
        self._thing_uuid = None

    def _fetch_thing_uuid(self):
        query = (
            "select thing_id as thing_uuid from public.sms_datastream_link l "
            "join public.sms_device_mount_action a on l.device_mount_action_id = a.id "
            "where a.configuration_id = %s"
        )
        with self._conn.cursor() as cur:
            row = cur.execute(query, [self.thing_id]).fetchone()
        self._thing_uuid = row[0]

    def _fetch(
        self, date_start: TimestampT, date_end: TimestampT, limit: int | None = None
    ) -> pd.DataFrame:
        """
        Fetch data between two datetimes from the database.
        Returns a pandas Series with datetime index.
        """

        # Note that, limit=None translates to 'LIMIT NULL'
        # in postgres which is equivalent to 'LIMIT ALL',
        # which effectively disables the limit for the query.
        query = sql.SQL(
            """
            select o.result_time, o.result_type, o.result_number, o.result_string, 
                   o.result_json, o.result_boolean, o.result_quality, o.datastream_id
            from observation o
            join datastream d on o.datastream_id = d.id
            join thing t on d.thing_id = t.id
            where t.uuid = %s
              and d.position = %s
              and o.result_time >= %s
              and o.result_time <= %s
            order by o.result_time desc
            limit %s
            """
        )

        with self._conn.cursor() as cur:
            cur.execute("set searchpath to %s", [self.schema])
            # The name is the stream alias and has the
            # form T{STA_THING_ID}S{AnyUserGivenName} e.g. 'T42Ssomefoo'
            pos = self.name.split("S", maxsplit=1)[1]
            cur.execute(query, (self._thing_uuid, pos, date_start, date_end, limit))

            data = None
            index = pd.DatetimeIndex([])
            if cur.rowcount > 0:
                timestamps, data = zip(*map(_extract, cur))
                index = pd.to_datetime(timestamps)

        return pd.DataFrame(data, columns=self._columns, index=index)

    def get_unprocessed_range(self) -> tuple[None, None]:
        """
        Returns (None, None) tuple, because data products
        quality labels are always created (and uploaded)
        at the same time and therefore the data never qualifys
        as __unprocessed__ data.
        """
        return None, None

    def get_data(
        self,
        date_start: TimestampT,
        date_end: TimestampT,
        context_window: WindowT,
    ) -> pd.Series:
        if self._thing_uuid is None:
            self._fetch_thing_uuid()
        return super().get_data(date_start, date_end, context_window)

    def set_data(self, data: pd.Series, qlabels: pd.DataFrame | None = None) -> None:
        """Sets new data uncondidionally."""
        index = data.index
        if data.empty:
            index = pd.DatetimeIndex([])
        assert isinstance(index, pd.DatetimeIndex)

        self._data = pd.DataFrame(columns=self._columns, index=index)
        self._data["data"] = data

        if qlabels is not None:
            self.update_quality_labels(qlabels)

    def upload(self, overwrite=True):
        """Update locally stored data and quality labels to the DB"""
        pass  # todo: Upload data and quality labels


class LocalStream(Datastream):

    def __init__(
        self,
        thing_id: int | None,
        stream_id: int | None,
        name: str,
        db_conn: psycopg.Connection | None,
        schema: str | None,
    ):
        super().__init__(thing_id, stream_id, name, db_conn, schema)

    def _append(self, *args, **kwargs):
        raise NotImplementedError

    def _fetch(self, *args, **kwargs):
        raise NotImplementedError

    def _fetch_context(self, *args, **kwargs):
        raise NotImplementedError

    def get_data(
        self,
        date_start: TimestampT | None,
        date_end: TimestampT | None,
        context_window: WindowT,
    ) -> pd.Series:

        # We can only get present data - in contrast to Datastream we
        # do not fetch data from the DB.

        data = self._data
        if context_window == 0:
            # None is handled gracefully with slices
            return data.loc[date_start:date_end, "data"]

        # Note that this also works for empty data !
        if date_start is None:
            date_start = data.index.min()
        if date_end is None:
            date_end = data.index.max()

        if isinstance(context_window, pd.Timedelta):
            new_start = date_start - context_window
            return data.loc[new_start:date_end, "data"]

        assert isinstance(context_window, int)
        chunk: pd.Series = data.loc[date_start:date_end, "data"]
        pre_chunk = data.loc[:date_start, "data"]
        context: pd.Series = pre_chunk.iloc[-(context_window + 1) : -1]
        return pd.concat([context, chunk])

    def set_data(self, data: pd.Series, qlabels: pd.Series | None = None) -> None:
        return ProductStream.set_data(self, data, qlabels)  # noqa

    def get_unprocessed_range(
        self,
    ) -> tuple[TimestampT, TimestampT] | tuple[None, None]:
        return None, None

    def upload(self, overwrite=True):
        raise RuntimeError("Temporary variables must not be uploaded to the DB.")
