#!/usr/bin/env python3
from __future__ import annotations

import typing
from typing import Any
from datetime import datetime

import pandas as pd
import psycopg
from psycopg import sql

if typing.TYPE_CHECKING:
    from timeio.qc.typeshints import TimestampT, WindowT

__all__ = [
    "Datastream",
    "ProductStream",
    "LocalStream",
]

""" 
This module provides a convenient abstraction for retrieving and 
storing datastreams from/to the users observation database.
"""


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
    """
    A Datastream for immutable existing data.

    The data can be retrieved from the DB. Quality annotations can be added
    and uploaded to the DB, but the data itself is readonly.
    """

    _columns = ["data", "quality", "stream_id"]

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
        Returns a pandas Dataframe with datetime index.
        """
        # Note that, limit=None translates to 'LIMIT NULL'
        # in postgres which is equivalent to 'LIMIT ALL',
        # which effectively disables the limit for the query.
        #
        # See also ProductStream._fetch which basically do
        # the same query on different tables.
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
            cur.execute("set search_path to %s", [self.schema])
            cur.execute(query, (self.stream_id, date_start, date_end, limit))

            data = None
            index = pd.DatetimeIndex([])
            if cur.rowcount > 0:
                timestamps, data = zip(*map(_extract, cur))
                index = pd.to_datetime(timestamps)

        return pd.DataFrame(data, columns=self._columns, index=index)

    def _fetch_context(self, date_start: TimestampT, window: WindowT) -> pd.Timestamp:
        """Fetches the context window and returns its first timestamp."""
        present_data_start = self._data.index.min()

        if isinstance(window, pd.Timedelta):
            new_start = date_start - window
            if new_start < present_data_start:
                fetched = self._fetch(new_start, present_data_start)
                self._append(fetched)
            return new_start

        assert isinstance(window, int)
        # We must account that pandas is inclusive and the
        # context-window is the number of data points BEFORE
        # the first data to process. The query to fetch the
        # data also includes the start and end dates. With
        # (windows+1) we always have an overlap of exactly one
        # observation between the data and the context data,
        # but this is acceptable.
        window += 1
        nr_obs = window - len(self._data.loc[:date_start])
        if nr_obs > 1:
            fetched = self._fetch("-Infinity", present_data_start, limit=nr_obs)
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
    ) -> pd.DataFrame:
        """
        Return data between date_start and date_end.
        Fetch missing data from DB if needed.
        Return dataframe with columns: [data, quality, stream_id]
        """
        if date_start is None:
            return pd.DataFrame([], pd.DatetimeIndex([]), self._columns, "object")

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
        return self._data.loc[context_start:date_end, self._columns]

    def __repr__(self):
        klass = self.__class__.__name__
        return (
            f"{klass}({self.thing_id}, {self.stream_id}, {self.name}, "
            f"cached={len(self._data.index)} rows)"
        )

    def update_quality_labels(self, labels: pd.Series | pd.DataFrame) -> None:
        """
        This acts like uploading data to the DB, but instead of
        really uploading the data, the data is stored within the
        stream abstraction (this class).

        labels must be a datetime indexed Dataframe with a 'quality'
        column holding the quality labels, OR a pandas.Series containing
        only the quality labels.
        """
        assert isinstance(labels.index, pd.DatetimeIndex)
        unknown = labels.index.difference(self._data.index)
        if not unknown.empty:
            pass  # todo warn about unknown labels
        index = labels.index.intersection(self._data.index)

        if isinstance(labels, pd.DataFrame):
            labels = labels["quality"]

        self._data.loc[index, "quality"] = labels.loc[index]

    def upload(self, overwrite=True):
        """Update locally stored quality labels to the DB"""
        pass  # todo: Upload quality labels


Datastream = DatastreamSTA


class ProductStream(Datastream):
    """
    A Datastream for mutable data a.k.a. Dataproducts.

    It never has  _unprocessed_ data, because the data is always generated
    by user defined algorithms. In contrast to a default datastream.Datastream,
    new data can be added and uploaded to the DB.
    """

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
        #
        # See also DatastreamSTA._fetch which basically do
        # the same query on different tables.
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

        return pd.DataFrame(data, index=index, columns=self._columns, dtype="object")

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
    ) -> pd.DataFrame:
        if self._thing_uuid is None:
            self._fetch_thing_uuid()
        return super().get_data(date_start, date_end, context_window)

    def set_data(self, data: pd.Series | pd.DataFrame) -> None:
        """Sets new data unconditionally.
        Data must be a Dataframe with a 'data' and a 'quality'
        column holding the data and the quality labels respectively,
        OR a pandas.Series containing only the data.
        """
        index = data.index
        if data.empty:
            index = pd.DatetimeIndex([])
        assert isinstance(index, pd.DatetimeIndex)

        self._data = pd.DataFrame(columns=self._columns, index=index)
        if isinstance(data, pd.Series):
            self._data["data"] = data
        else:
            self._data["data"] = data["data"]
            self._data["quality"] = data["quality"]

    def upload(self, overwrite=True):
        """Update locally stored data and quality labels to the DB"""
        pass  # todo: Upload data and quality labels


class LocalStream(Datastream):
    """
    A Datastream for temporary local data.

    Its data is never uploaded to the DB.
    """

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
    ) -> pd.DataFrame:

        # We can only get present data - in contrast to Datastream we
        # do not fetch data from the DB.

        data = self._data
        if context_window == 0:
            # None is handled gracefully with slices
            return data.loc[date_start:date_end, self._columns]

        # Note that this also works for empty data !
        if date_start is None:
            date_start = data.index.min()
        if date_end is None:
            date_end = data.index.max()

        if isinstance(context_window, pd.Timedelta):
            new_start = date_start - context_window
            return data.loc[new_start:date_end, self._columns]

        assert isinstance(context_window, int)
        chunk: pd.DataFrame = data.loc[date_start:date_end, self._columns]
        pre_chunk = data.loc[:date_start, self._columns]
        context: pd.DataFrame = pre_chunk.iloc[-(context_window + 1) : -1]
        return pd.concat([context, chunk], axis=0)

    def set_data(self, data: pd.DataFrame) -> None:
        return ProductStream.set_data(self, data)

    def get_unprocessed_range(
        self,
    ) -> tuple[TimestampT, TimestampT] | tuple[None, None]:
        return None, None

    def upload(self, overwrite=True):
        raise RuntimeError("Temporary data cannot be uploaded to the DB.")
