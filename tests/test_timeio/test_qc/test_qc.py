#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

import numpy as np
import pandas as pd

from timeio.common import get_envvar
from timeio.databases import Database
from timeio.qc import get_functions_to_execute
from timeio.qc.qcfunction import QcFunction, StreamInfo
from timeio.qc.utils import load_data, write_data
from timeio.qc.saqc import SaQCWrapper

TEST_FUNCTIONS = [
    QcFunction(
        "Static-T1",
        context_window=0,
        func_name="flagRange",
        fields=[StreamInfo(key="field", alias="T1S33", sta_thing_id=1, sta_stream_id=33)],
        targets=[StreamInfo(key="target", alias="T1S33", sta_thing_id=1, sta_stream_id=33)],
        params={"min": 900, "max": 1200},
    ),
    QcFunction(
        "Static-T2",
        context_window=0,
        func_name="flagRange",
        fields=[StreamInfo("field", "T1S36", 1, 36)],
        targets=[StreamInfo("target", "T1S36", 1, 36)],
        params={"min": 900, "max": 1200},
    ),
    QcFunction(
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
    QcFunction(
        "Dynamic-T1",
        context_window=0,
        func_name="flagRange",
        fields=[StreamInfo("field", "T2S44", 4, 44)],
        targets=[StreamInfo("target", "T2S44", 4, 44)],
        params={"min": 0, "max": 15},
    ),
    QcFunction(
        "Dynamic-T2",
        context_window=0,
        func_name="flagUniLOF",
        fields=[StreamInfo("field", "T2S46", 4, 46)],
        targets=[StreamInfo("target", "T2S46", 4, 46)],
        params={},
    ),
    QcFunction(
        "Dynamic-P1",
        context_window=0,
        func_name="copyField",
        fields=[StreamInfo("field", "T1S27", 1, 27)],
        targets=[StreamInfo("target", "T2S43", None, None)],
        params={"overwrite": True},
    ),
]


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
        "T1S27": pd.DataFrame(
            data={"data": [4.5, 4.6, 3.9, 4.1], "quality": None}, index=index
        ),
    }


@pytest.mark.parametrize(
    "thing_id, expected",
    [
        (1, ("Static-T1", "Static-T2", "Static-P1", "Dynamic-P1")),
        (4, ("Dynamic-T1", "Dynamic-T2")),
    ],
)
def test_collect_tests(thing_id, expected):
    qc_functions = [
        QcFunction(
            "Static-T1",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo(key="field", alias="T1S33", sta_thing_id=1, sta_stream_id=33)],
            targets=[StreamInfo(key="target", alias="T1S33", sta_thing_id=1, sta_stream_id=33)],
            params={"min": 900, "max": 1200},
        ),
        QcFunction(
            "Static-T2",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo("field", "T1S36", 1, 36)],
            targets=[StreamInfo("target", "T1S36", 1, 36)],
            params={"min": 900, "max": 1200},
        ),
        QcFunction(
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
        QcFunction(
            "Dynamic-T1",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo("field", "T2S44", 4, 44)],
            targets=[StreamInfo("target", "T2S44", 4, 44)],
            params={"min": 0, "max": 15},
        ),
        QcFunction(
            "Dynamic-T2",
            context_window=0,
            func_name="flagUniLOF",
            fields=[StreamInfo("field", "T2S46", 4, 46)],
            targets=[StreamInfo("target", "T2S46", 4, 46)],
            params={},
        ),
        QcFunction(
            "Dynamic-P1",
            context_window=0,
            func_name="copyField",
            fields=[StreamInfo("field", "T1S27", 1, 27)],
            targets=[StreamInfo("target", "T2S43", None, None)],
            params={"overwrite": True},
        ),
    ]

    tests = get_functions_to_execute(qc_functions, thing_id)
    assert set(set([t.name for t in tests])) == set(expected)


@pytest.mark.parametrize(
    "func, data_in, data_out",
    [
        (
            QcFunction(
                "",
                func_name="flagRange",
                fields=[
                    StreamInfo(key="field", alias="T1S33", sta_thing_id=1, sta_stream_id=33)
                ],
                targets=[
                    StreamInfo(key="target", alias="T1S33", sta_thing_id=1, sta_stream_id=33)
                ],
                params={"min": 900, "max": 1200},
            ),
            {StreamInfo("field", "T1S33"): [800, 900, 1000, 1250]},
            {StreamInfo("target", "T1S33"): [255, -np.inf, -np.inf, 255]},
        ),
    ],
)
def test_qc_function_execution(func, data_in, data_out):

    data_in = {k: pd.DataFrame({"data": v}) for k, v in data_in.items()}
    # set some datastream ids
    for i, v in enumerate(data_in.values()):
        v.attrs["stream_id"] = i

    qc = init_saqc(data_in)
    qc = execute_qc_function(qc, func)

    for stream in data_in.keys():
        assert (qc._flags[stream.name] == data_out[stream]).all()
        assert (qc.data[stream.name] == data_in[stream]["data"]).all()


@pytest.mark.parametrize(
    "func, data_in, data_out",
    [
        # (
        #     QcFunction(
        #         "",
        #         func_name="copyField",
        #         fields=[StreamInfo("field", "SRC", 1, 27)],
        #         targets=[StreamInfo("target", "TRG", None, None)],
        #         params={"overwrite": True},
        #     ),
        #     {StreamInfo("field", "SRC"): [4.5, 4.6, 3.9, 4.1]},
        #     {
        #         StreamInfo("field", "SRC"): [4.5, 4.6, 3.9, 4.1],
        #         StreamInfo("target", "TRG"): [4.5, 4.6, 3.9, 4.1],
        #     },
        # ),
        (
            QcFunction(
                "",
                func_name="processGeneric",
                fields=[
                    StreamInfo("field", "SRC_1", 1, 33),
                    StreamInfo("field", "SRC_2", 1, 36),
                ],
                targets=[StreamInfo("target", "TRG", None, None)],
                params={"func": "(SRC_1 + SRC_2) / 2"},
            ),
            {
                StreamInfo("field", "SRC_1"): [900, 910, 920, 930],
                StreamInfo("field", "SRC_2"): [800, 810, 820, 830],
            },
            {
                StreamInfo("field", "SRC_1"): [900, 910, 920, 930],
                StreamInfo("field", "SRC_2"): [800, 810, 820, 830],
                StreamInfo("target", "TRG"): [850, 860, 870, 880],
            },
        ),
    ],
)
def test_processing_function_execution(func, data_in, data_out):
    qc = init_saqc(data_in)
    qc = execute_qc_function(qc, func)
    for stream, data in data_out.items():
        assert (qc.data[stream.name] == data).all()

    data = exit_saqc(qc)


def test_db_data_reading(local_database_connection):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres"
    # is available
    fields = [
        StreamInfo(key="field", alias="T1S27", sta_thing_id=1, sta_stream_id=27),
        StreamInfo(key="field", alias="T1S33", sta_thing_id=1, sta_stream_id=33),
        StreamInfo(key="field", alias="T1S36", sta_thing_id=1, sta_stream_id=36),
        StreamInfo(key="field", alias="T2S44", sta_thing_id=4, sta_stream_id=44),
        StreamInfo(key="field", alias="T2S46", sta_thing_id=4, sta_stream_id=46),
    ]
    data = load_data(local_database_connection, streams=fields)
    assert data.keys() == {"T1S33", "T1S36", "T2S44", "T2S46", "T1S27"}

    for df in data.values():
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"data", "quality"}


def test_db_data_writing(local_database_connection):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres"
    # is available

    # fields = [
    #     StreamInfo(key="field", name="T1S27", thing_id=1, stream_id=27),
    #     StreamInfo(key="field", name="T1S33", thing_id=1, stream_id=33),
    #     StreamInfo(key="field", name="T1S36", thing_id=1, stream_id=36),
    #     StreamInfo(key="field", name="T2S44", thing_id=4, stream_id=44),
    #     StreamInfo(key="field", name="T2S46", thing_id=4, stream_id=46),
    # ]
    # df1 = pd.DataFrame(
    #     {"data": [900, 300, 100], "quality": [255, -np.inf, -np.inf]},
    #     index=pd.date_range("2022-01-01", freq="D", periods=3),
    # )
    # df2 = pd.DataFrame(
    #     {"data": [4.6, 4.7, 4.8, 4.9], "quality": [-np.inf, -np.inf, 255, 255]},
    #     index=pd.date_range("2022-06-01", freq="M", periods=4),
    # )

    # data = {
    #     StreamInfo(key="field", name="T1S27", thing_id=1, stream_id=27): df1,
    #     StreamInfo(key="field", name="T2S44", thing_id=4, stream_id=44): df2
    # }

    func = QcFunction(
                "",
                func_name="processGeneric",
                fields=[
                    StreamInfo(key="field", alias="T1S27", sta_thing_id=1, sta_stream_id=27),
                ],
                targets=[
                    StreamInfo(key="field", alias="NEW", sta_thing_id=1, sta_stream_id=None),
                ],
                params={"func": "T1S27 + 5"},
            )

    fields = [
        StreamInfo(key="field", alias="T1S27", sta_thing_id=1, sta_stream_id=27),
        StreamInfo(key="field", alias="T1S33", sta_thing_id=1, sta_stream_id=33),
        StreamInfo(key="field", alias="T1S36", sta_thing_id=1, sta_stream_id=36),
        StreamInfo(key="field", alias="T2S44", sta_thing_id=4, sta_stream_id=44),
        StreamInfo(key="field", alias="T2S46", sta_thing_id=4, sta_stream_id=46),
    ]
    data = load_data(local_database_connection, streams=fields)
    qc = SaQCWrapper(data)

    api_url = "http://localhost:8001"

    qc.execute(func)

    write_data(local_database_connection, qc, api_url)
    # qc_out = execute_qc_function(qc, func)
    # import ipdb; ipdb.set_trace()



    # data = load_data(local_database_connection, streams=fields)
    # assert data.keys() == {"T1S33", "T1S36", "T2S44", "T2S46", "T1S27"}
    # for df in data.values():
    #     assert isinstance(df, pd.DataFrame)
    #     assert set(df.columns) == {"data", "quality"}
