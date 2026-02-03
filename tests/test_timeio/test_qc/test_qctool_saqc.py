#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

import numpy as np
import pandas as pd

from timeio.databases import Database
from timeio.qc import get_functions_to_execute
from timeio.qc.qctest import QcTest, StreamInfo
from timeio.qc.utils import load_data
from timeio.qc.saqc import init_saqc, execute_qc_function


@pytest.fixture()
def local_database_connection():
    dsn = "postgresql://postgres:postgres@localhost/postgres"
    try:
        conn = Database(dsn).connection()
    except ConnectionError:
        pytest.skip("local database connection not availan")

    yield conn
    conn.close()


@pytest.fixture()
def test_data():

    index = pd.date_range("2020-01-01", freq="D", periods=4)
    return {
        "T1S33": pd.DataFrame(
            data={"data": [800, 1000, 1100, 1300], "quality": None}, index=index
        ),
        "T1S36": pd.DataFrame(
            data={"data": [750, 950, 1050, 1250], "quality": None}, index=index
        ),
    }


@pytest.fixture()
def qc_functions():
    return [
        QcTest(
            "Static-T1",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo(key="field", name="T1S33", thing_id=1, stream_id=33)],
            targets=[StreamInfo(key="target", name="T1S33", thing_id=1, stream_id=33)],
            params={"min": 900, "max": 1200},
        ),
        QcTest(
            "Static-T2",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo("field", "T1S36", 1, 36)],
            targets=[StreamInfo("target", "T1S36", 1, 36)],
            params={"min": 900, "max": 1200},
        ),
        QcTest(
            "Static-P1",
            context_window=0,
            func_name="processGeneric",
            fields=[
                StreamInfo("field", "T1S33", 1, 33),
                StreamInfo("field", "T1S36", 1, 36),
            ],
            targets=[StreamInfo("target", "T1S99", None, None)],
            params={"func": "lambda x, y: (x + y)/2"},
        ),
        QcTest(
            "Dynamic-T1",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo("field", "T2S44", 4, 44)],
            targets=[StreamInfo("target", "T2S44", 4, 44)],
            params={"min": 0, "max": 15},
        ),
        QcTest(
            "Dynamic-T2",
            context_window=0,
            func_name="flagUniLOF",
            fields=[StreamInfo("field", "T2S46", 4, 46)],
            targets=[StreamInfo("target", "T2S46", 4, 46)],
            params={},
        ),
        QcTest(
            "Dynamic-P1",
            context_window=0,
            func_name="copyField",
            fields=[StreamInfo("field", "T1S27", 1, 27)],
            targets=[StreamInfo("target", "T2S43", 4, 43)],
            params={"overwrite": True},
        ),
    ]


@pytest.mark.parametrize(
    "thing_id, expected",
    [
        (1, ("Static-T1", "Static-T2", "Static-P1", "Dynamic-P1")),
        (4, ("Dynamic-T1", "Dynamic-T2")),
    ],
)
def test_collect_tests(qc_functions, thing_id, expected):
    tests = get_functions_to_execute(qc_functions, thing_id)
    assert set(set([t.name for t in tests])) == set(expected)


def test_db_data_loading(local_database_connection, qc_functions):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres"
    # is available

    fields = []
    for f in qc_functions:
        fields.extend(f.fields)

    data = load_data(local_database_connection, streams=fields)
    assert data.keys() == {"T1S33", "T1S36", "T2S44", "T2S46", "T1S27"}
    for df in data.values():
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"data", "quality"}


def test_function_execution(qc_functions, test_data):

    index = tuple(test_data.values())[0].index
    qc = init_saqc(test_data)

    for func in qc_functions[:2]:
        qc = execute_qc_function(qc, func)

    assert qc._flags["T1S33"].equals(
        pd.Series([255.0, -np.inf, -np.inf, 255.0], index=index)
    )
    assert qc.data["T1S33"].equals(pd.Series([800, 1000, 1100, 1300], index=index))

    assert qc._flags["T1S36"].equals(
        pd.Series([255.0, -np.inf, -np.inf, 255.0], index=index)
    )
    assert qc.data["T1S36"].equals(pd.Series([750, 950, 1050, 1250], index=index))


@pytest.mark.xfail
def test_generic_function_execution(qc_functions, test_data):
    qc = init_saqc(test_data)
    qc = execute_qc_function(qc, qc_functions[2])
