#!/usr/bin/env python3

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import requests
import pandas as pd

import psycopg
from psycopg import sql

from timeio.errors import DataNotFoundError
from timeio.cast import rm_tz
from timeio.qc.typeshints import TimestampT


def _extract(row) -> tuple[datetime, tuple[Any, int, int]]:
    """
    This mainly extracts the data from the number-, string-,
    json-, or the boolean-columns. The info, which column holds
    the data is numerically encoded in the result_type column.
    We return a nested tuple:
        (RESULT_TIME, (DATA, QUALITY, RAW_STREAM_ID))
    """
    return row[0], (row[row[1] + 2], row[6], row[7])


class AbstractDatastreamRepository(ABC):
    @abstractmethod
    def upload(self, api_base_url: str, qc_labels):
        pass


class STADatastreamRepository(AbstractDatastreamRepository):

    def __init__(self, schema: str, db_conn: psycopg.Connection) -> None:
        self.schema = schema
        self._conn = db_conn
        self._thing = None
        self._columns = ["data", "quality", "stream_id"]

    def _fetch_thing_uuid(self, stream_id) -> str:
        q = sql.SQL(
            "select thing_id as thing_uuid from public.sms_datastream_link "  # noqa
            "where device_property_id = %s"
        ).format()
        with self._conn.cursor() as cur:
            row = cur.execute(q, [stream_id]).fetchone()
        if row is None:
            raise DataNotFoundError(f"Found no thing_uuid for {stream_id}")
        return row[0]

    def _fetch_data(
        self,
        stream_id,
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
        query = sql.SQL("""
            select "RESULT_TIME", "RESULT_TYPE", "RESULT_NUMBER", "RESULT_STRING",
                "RESULT_JSON", "RESULT_BOOLEAN", "RESULT_QUALITY",  l.datastream_id
            from "OBSERVATIONS" o
            join public.sms_datastream_link l on o."DATASTREAM_ID" = l.device_property_id
            where o."DATASTREAM_ID" = %s
              and o."RESULT_TIME" >= %s
              and o."RESULT_TIME" <= %s
            order by o."RESULT_TIME" desc
            limit %s
            """)

        if date_end in [None, pd.NaT]:
            date_end = "Infinity"

        with self._conn.cursor() as cur:
            cur.execute(sql.SQL("set search_path to {}").format(self.schema))
            cur.execute(query, (stream_id, date_start, date_end, limit))
            df = self._db_to_df(cur)

        return df

    def _db_to_df(self, cur: psycopg.Cursor) -> pd.DataFrame:
        data = None
        index = pd.DatetimeIndex([])
        if cur.rowcount > 0:
            timestamps, data = zip(*map(_extract, cur))
            index = pd.to_datetime(timestamps, utc=True)
            # To avoid errors from mixing TZ aware and TZ unaware objects.
            # We handle everything in UTC without TZ.
            index = rm_tz(index)

        return pd.DataFrame(data, index, self._columns, dtype=object)

    def upload(self, api_base_url: str, qc_labels):
        r = requests.post(
            f"{api_base_url}/observations/qaqc/{self._thing.uuid}",
            data=f'{{"qaqc_labels":{qc_labels}}}',
            headers={"Content-type": "application/json"},
        )
        r.raise_for_status()
