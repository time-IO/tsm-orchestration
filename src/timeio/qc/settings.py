#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import annotations

import abc
import datetime
import json
import logging
import subprocess
import sys
import typing
import warnings
from dataclasses import dataclass
from functools import partial
from typing import Any, Hashable, Literal, cast, Generic, TypeVar

import pandas as pd
import requests
import saqc
from psycopg import Connection, sql
from psycopg.rows import dict_row
from saqc import DictOfSeries, Flags

try:
    from psycopg_pool import ConnectionPool
except ImportError:
    ConnectionPool = typing.TypeVar("ConnectionPool")  # noqa

from timeio.common import ObservationResultType
from timeio.errors import DataNotFoundError, UserInputError, NoDataWarning
from timeio.typehints import DbRowT, JsonObjectT
from timeio.journaling import Journal
from timeio import feta

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")

from datetime import datetime
from typing import List, Tuple, Any
import bisect
import psycopg


class Datastream:

    def __init__(
        self, thing_id: str, stream_id: str, name: str, db_conn: psycopg.Connection
    ):
        self.thing_id = thing_id
        self.stream_id = stream_id
        self.name = name
        self._conn = db_conn
        self.data = pd.Series(dtype="object", index=pd.DatetimeIndex())

    def _fetch(self, start: datetime, end: datetime) -> pd.Series:
        """
        Fetch data between two datetimes from the database.
        Returns a pandas Series with datetime index.
        """

        # todo query
        query = """
            SELECT timestamp, value
            FROM measurements
            WHERE thing_id = %s
              AND stream_id = %s
              AND timestamp >= %s
              AND timestamp <= %s
            ORDER BY timestamp
        """
        with self._conn.cursor() as cur:
            cur.execute(query, (self.thing_id, self.stream_id, start, end))
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

    def get(self, start: datetime, end: datetime, context_window=None) -> pd.Series:
        """
        Return data between start and end.
        Fetch missing data from DB if needed.
        """
        if self.data.empty:
            self.data = self._fetch(start, end)
        else:
            missing_start = start < self.data.index.min()
            missing_end = end > self.data.index.max()

            if missing_start:
                fetched = self._fetch(start, self.data.index.min())
                self.data = fetched.combine_first(self.data)

            if missing_end:
                fetched = self._fetch(self.data.index.max(), end)
                self.data = self.data.combine_first(fetched)

        chunk = self.data.loc[start:end]
        if chunk.empty or context_window is None:
            return chunk

        context_start = self._fetch_context(start, context_window)
        return self.data.loc[context_start:end]

    def _fetch_context(self, start, window) -> datetime:
        """
        Fetches the context window and
        returns the timestamp of the first value.
        """
        # todo: fetch context by number or timedelta
        return start - window

    def __repr__(self):
        return (
            f"Datastream({self.thing_id}, {self.stream_id}, {self.name}, "
            f"cached={len(self.data)} rows)"
        )


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
TimestampT = typing.Union[datetime.timestamp, pd.Timestamp]


class SaQCFuncT(typing.Protocol):
    def __call__(self, qc: saqc.SaQC, *args: Any, **kwargs: Any) -> saqc.SaQC: ...


class Param:
    def __init__(self, name, value: Any, *args):
        self.name = name
        self.value = value

    def parse(self):
        # cast according to Datatype
        return self.value


class StreamParam(Param):
    def __init__(self, name, value: Any, thing_id, stream_id, *args):
        super().__init__(name, value, StreamParam)
        self.stream_id = stream_id
        self.thing_id = thing_id
        # todo: add alias parsing

    def parse(self):
        # cast according to Datatype
        return self.value


class QcTest:
    def __init__(self, name, func_name, params: list[Param], context_window=None):
        self.func_name = func_name
        self._params = params
        self._window = context_window

        # filled by QcTest.parse()
        self.name = name or "Unnamed QcTest"
        self.context_window = None
        self.args = {}
        self.streams: list[StreamParam] = []

    @classmethod
    def from_feta(cls, test: feta.QAQCTest):
        params = []
        for stream in test.streams or []:  # type: feta.QcStreamT
            params.append(
                StreamParam(
                    stream["arg_name"],
                    stream["sta_thing_id"],
                    stream["sta_stream_id"],
                    stream["alias"],
                )
            )
        for key, value in test.args.items():
            params.append(Param(key, value))
        return cls(test.name, test.function, params)

    def parse(self):
        self._parse_window()
        getattr(saqc.SaQC, self.func_name)
        for p in self._params:
            self.args[p.name] = p.parse()
            if isinstance(p, StreamParam):
                self.streams.append(p)

    def _parse_window(self):
        window = self._window
        if window is None:
            window = 0
        if isinstance(window, int) or isinstance(window, str) and window.isnumeric():
            window = int(window)
            is_negative = window < 0
        else:
            window = pd.Timedelta(window)
            is_negative = window.days < 0

        if is_negative:
            raise UserInputError(
                "Parameter 'context_window' must not have a negative value"
            )
        self.context_window = window


def upload(): ...


class QcTool(abc.ABC):

    @abc.abstractmethod
    def check_func_name(self, func_name: str) -> bool: ...

    def execute(
        self,
        func_name: str,
        data: dict[str, pd.Series],
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]: ...


class Saqc(QcTool):

    def check_func_name(self, func_name: str) -> bool:
        return hasattr(saqc.SaQC, func_name)

    def execute(self, func_name: str, data: dict[str, pd.Series], args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}

        qc = saqc.SaQC(data)
        func = getattr(qc, func_name)
        res: saqc.SaQC = func(*args, **kwargs)

        return dict(res.data), dict(res.flags)


class QcRealtime:
    def __init__(self, conf: feta.QAQC, runner: QcTool):
        self.conf = conf
        self.tests: list[QcTest] = []
        self.streams: dict[str, Datastream] = {}
        self._runner = runner

        self.collect_tests()
        self.collect_streams()
        self._data = None

    def collect_tests(self):
        for i, test in enumerate(self.conf.get_tests()):  # type: int, feta.QAQCTest
            self.tests.append(QcTest.from_feta(test))

    def collect_streams(self):
        for test in self.tests:
            for s in test.streams:
                if s.name not in self.streams:
                    ds = Datastream(s.thing_id, s.stream_id, s.name)
                    self.streams[s.name] = ds

    def _prep_data(self, test: QcTest):
        data = []
        for p in test.streams:  # type: StreamParam
            start, end = self.streams[p.name].get_unflagged_range()
            data[p.name] = self.streams[p.name].get(start, end, test.context_window)
        self._data = data

    def _parse(self, test: QcTest):
        test.parse()

    def _execute(self, test: QcTest):
        data, flags = self._runner.execute(test.func_name, self._data, (), test.args)

    def run(self):
        for test in self.tests:
            self._parse(test)
            self._prep_data(test)
            self._execute(test)


def run_scheduled(start, end):
    tests = collect_tests(...)
    streams = collect_streams(tests)
    for test in tests:
        streams = run_test(test, streams)


# get all QC test from DB
# parse everything that is user input - (freetext function - values)
# insert all streams to streamManager
# fetch neccessary data
# run test
