#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from datetime import datetime

import pandas as pd

from timeio.qc import get_qc_functions_to_execute
from timeio.qc.qctest import QcTest, StreamInfo, Param
from timeio.qc.datastream import (
    AbstractDatastream,
    AbstractDatastreamFactory,
    ProductStream,
    LocalStream,
    STADatastream,
)
from timeio.qc.typeshints import TimestampT, WindowT

# NEXT:
# - abstract the direct database connections out of STADatastream, ProductStream et al


class MockDatastream(AbstractDatastream):
    def get_unprocessed_range(
        self,
    ) -> tuple[TimestampT, TimestampT] | tuple[None, None]:
        return (datetime(2020, 1, 1, 12, 0, 0), datetime(2020, 1, 2, 12, 0, 0))

    def get_data(
        self,
        date_start: TimestampT | None,
        date_end: TimestampT | None,
        context_window: WindowT,
    ) -> pd.DataFrame:

        return pd.DataFrame()


class MockDatastreamFactory(AbstractDatastreamFactory):
    def create(self, stream_info):
        tid = stream_info.thing_id
        sid = stream_info.stream_id
        name = stream_info.value
        schema = "ttt"

        if stream_info.is_dataproduct:
            return ProductStream(tid, sid, name, self._conn, schema)
        if stream_info.is_temporary:
            return LocalStream(tid, sid, name, self._conn, schema)
        return STADatastream(tid, sid, name, self._conn, schema)


@pytest.fixture()
def qc_functions():
    return [
        QcTest(
            "Static-T1",
            context_window=0,
            qctool="saqc",
            func_name="flagRange",
            params=[
                StreamInfo(key="field", value="T1S33", thing_id=1, stream_id=33),
                StreamInfo(key="target", value="T1S33", thing_id=1, stream_id=33),
                Param(key="max", value=1200),
                Param(key="min", value=900),
            ],
        ),
        QcTest(
            "Static-T2",
            context_window=0,
            qctool="saqc",
            func_name="flagRange",
            params=[
                StreamInfo("field", "T1S36", 1, 36),
                StreamInfo("target", "T1S36", 1, 36),
                Param("max", 1200),
                Param("min", 900),
            ],
        ),
        QcTest(
            "Static-P1",
            context_window=0,
            qctool="saqc",
            func_name="processGeneric",
            params=[
                StreamInfo("field", "T1S33", 1, 33),
                StreamInfo("target", "T1S36", 1, 36),
                StreamInfo("target", "T1S33", 1, 33),
                StreamInfo("target", "T1S36", 1, 36),
                Param("func", "lambda x, y: (x + y)/2"),
            ],
        ),
        QcTest(
            "Dynamic-T1",
            context_window=0,
            qctool="saqc",
            func_name="flagRange",
            params=[
                StreamInfo("field", "T2S44", 2, 44),
                StreamInfo("target", "T2S44", 2, 44),
                Param("max", 15),
                Param("min", 0),
            ],
        ),
        QcTest(
            "Dynamic-T2",
            context_window=0,
            qctool="saqc",
            func_name="flagUniLOF",
            params=[
                StreamInfo("field", "T2S46", 2, 46),
                StreamInfo("target", "T2S46", 2, 46),
            ],
        ),
        QcTest(
            "Dynamic-P1",
            context_window=0,
            qctool="saqc",
            func_name="copyField",
            params=[
                StreamInfo("field", "T1S27", 1, 27),
                StreamInfo("target", "T2S43", 2, 43),
                Param("overwrite", True),
            ],
        ),
    ]


@pytest.mark.parametrize(
    "thing_id, expected",
    [
        (1, ("Static-T1", "Static-T2", "Static-P1", "Dynamic-P1")),
        (2, ("Dynamic-T1", "Dynamic-T2")),
    ],
)
def test_collect_tests(qc_functions, thing_id, expected):
    tests = get_qc_functions_to_execute(qc_functions, thing_id)
    assert set(set([t.name for t in tests])) == set(expected)
