#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import annotations

import logging
import typing
import warnings

import pandas as pd
import saqc

from timeio.qc.datastream import Datastream
from timeio.qc.qctest import QcTest, StreamParam, Param
from timeio.qc.qctools import QcTool

try:
    from psycopg_pool import ConnectionPool
except ImportError:
    ConnectionPool = typing.TypeVar("ConnectionPool")  # noqa

from timeio import feta

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")

from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
TimestampT = typing.Union[datetime.timestamp, pd.Timestamp]


class SaQCFuncT(typing.Protocol):
    def __call__(self, qc: saqc.SaQC, *args: Any, **kwargs: Any) -> saqc.SaQC: ...


def upload(): ...


class QcRealtime:
    def __init__(self, conf: feta.QAQC, qctool: QcTool):
        self.conf = conf
        self.tests: list[QcTest] = []
        self.streams: dict[str, Datastream] = {}
        self._qctool = qctool

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
        test.parse(self._qctool)

    def _execute(self, test: QcTest):
        data, annos = self._qctool.execute(test.func_name, self._data, (), test.args)

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
