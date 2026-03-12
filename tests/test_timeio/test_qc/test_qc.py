#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

import numpy as np
import pandas as pd

from timeio.databases import Database, DBapi
from timeio.qc import filter_functions
from timeio.qc.qcfunction import QcFunction, StreamInfo, get_functions
from timeio.qc.io import read_stream_data, write_qc_data
from timeio.qc.saqc import SaQCWrapper
from timeio import feta

"""
TODO:
- test context window
"""


@pytest.fixture()
def local_database():
    dsn = "postgresql://postgres:postgres@localhost/postgres"
    try:
        conn = Database(dsn).connection()
    except ConnectionError:
        pytest.skip("local database connection not available")

    yield conn
    conn.close()


@pytest.fixture()
def local_dbapi():
    # TODO: try to get from .env file
    url = "http://localhost:8001"
    token = "local_bearer_token_processing"
    try:
        return DBapi(base_url=url, auth_token=token)
    except ConnectionError:
        pytest.skip("local dbapi connection not available")


T1S27 = StreamInfo(
    key="field",
    alias="T1S27",
    sta_thing_id=1,
    sta_stream_id=27,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="3e23c121-6a6e-48ac-9fb6-9d9a5bf06348",
    datastream_id=15,
    context_window=pd.Timedelta(0),
    position="N1Cts",
)
T1S33 = StreamInfo(
    key="field",
    alias="T1S33",
    sta_thing_id=1,
    sta_stream_id=33,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="3e23c121-6a6e-48ac-9fb6-9d9a5bf06348",
    datastream_id=3,
    context_window=pd.Timedelta(0),
    position="P1_mb",
)
T1S36 = StreamInfo(
    key="field",
    alias="T1S36",
    sta_thing_id=1,
    sta_stream_id=36,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="3e23c121-6a6e-48ac-9fb6-9d9a5bf06348",
    datastream_id=4,
    context_window=pd.Timedelta(0),
    position="P3_mb",
)
T2S44 = StreamInfo(
    key="field",
    alias="T2S44",
    sta_thing_id=2,
    sta_stream_id=44,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="f3691b96-aca1-4585-95bf-6ea4c611503c",
    datastream_id=34,
    context_window=pd.Timedelta(0),
    position="TMet20",
)
T2S43 = StreamInfo(
    key="field",
    alias="T2S43",
    sta_thing_id=2,
    sta_stream_id=43,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="f3691b96-aca1-4585-95bf-6ea4c611503c",
    datastream_id=24,
    context_window=pd.Timedelta(0),
    position="RecordNum",
)
T2S46 = StreamInfo(
    key="field",
    alias="T2S46",
    sta_thing_id=2,
    sta_stream_id=46,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="f3691b96-aca1-4585-95bf-6ea4c611503c",
    datastream_id=36,
    context_window=pd.Timedelta(0),
    position="N01C",
)
NEW = StreamInfo(
    key="target",
    alias="NEW",
    sta_thing_id=2,
    sta_stream_id=None,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="f3691b96-aca1-4585-95bf-6ea4c611503c",
    datastream_id=None,
    context_window=pd.Timedelta(0),
    position="NEW",
)


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
        (2, ("Dynamic-T1", "Dynamic-T2")),
    ],
)
def test_collect_tests(thing_id, expected):
    qc_functions = [
        QcFunction(
            "Static-T1",
            func_name="flagRange",
            fields=[T1S33],
            params={"min": 900, "max": 1200},
        ),
        QcFunction(
            "Static-T2",
            func_name="flagRange",
            fields=[T1S36],
            params={"min": 900, "max": 1200},
        ),
        QcFunction(
            "Static-P1",
            func_name="processGeneric",
            fields=[T1S33, T1S36],
            targets=[NEW],
            params={"func": "(T1S33 + T1S36)/2"},
        ),
        QcFunction(
            "Dynamic-T1",
            func_name="flagRange",
            fields=[T2S44],
            params={"min": 0, "max": 15},
        ),
        QcFunction("Dynamic-T2", func_name="flagUniLOF", fields=[T2S46], params={}),
        QcFunction(
            "Dynamic-P1",
            func_name="copyField",
            fields=[T1S27],
            targets=[T2S43],
            params={"overwrite": True},
        ),
    ]

    tests = filter_functions(qc_functions, thing_id)
    assert set(set([t.name for t in tests])) == set(expected)


@pytest.mark.parametrize(
    "func, data_in, data_out",
    [
        (
            QcFunction(
                "TEST",
                func_name="flagRange",
                fields=[T1S33],
                params={"min": 900, "max": 1200},
            ),
            {T1S33: [800, 900, 1000, 1250]},
            {T1S33: [255, -np.inf, -np.inf, 255]},
        ),
    ],
)
def test_qc_function_execution(func, data_in, data_out):

    data_in = {k: pd.DataFrame({"data": v}) for k, v in data_in.items()}
    # set some datastream ids
    for i, v in enumerate(data_in.values()):
        v.attrs["stream_id"] = i

    qc = SaQCWrapper(data_in)
    qc.execute(func)

    for stream in data_in.keys():
        assert (qc._qc._flags[stream.alias] == data_out[stream]).all()
        assert (qc._qc.data[stream.alias] == data_in[stream]["data"]).all()


@pytest.mark.parametrize(
    "func, data_in, data_out",
    [
        (
            QcFunction(
                "TEST",
                func_name="copyField",
                fields=[T1S27],
                targets=[NEW],
                params={"overwrite": True},
            ),
            {T1S27: [4.5, 4.6, 3.9, 4.1]},
            {
                T1S27: [4.5, 4.6, 3.9, 4.1],
                NEW: [4.5, 4.6, 3.9, 4.1],
            },
        ),
        (
            QcFunction(
                "",
                func_name="processGeneric",
                fields=[T1S33, T1S36],
                targets=[NEW],
                params={"func": "(T1S33 + T1S36) / 2"},
            ),
            {
                T1S33: [900, 910, 920, 930],
                T1S36: [800, 810, 820, 830],
            },
            {
                T1S33: [900, 910, 920, 930],
                T1S36: [800, 810, 820, 830],
                NEW: [850, 860, 870, 880],
            },
        ),
    ],
)
def test_processing_function_execution(func, data_in, data_out):

    data_in = {k: pd.DataFrame({"data": v}) for k, v in data_in.items()}
    qc = SaQCWrapper(data_in)

    qc.execute(func)
    for stream, data in data_out.items():
        assert (qc.data[stream]["data"] == data).all()


def test_db_data_reading(local_database):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres" is available
    fields = [T1S27, T1S33, T1S36, T2S44, T2S46]

    data = read_stream_data(local_database, streams=fields)

    assert {s.alias for s in data.keys()} == {
        "T1S33",
        "T1S36",
        "T2S44",
        "T2S46",
        "T1S27",
    }

    for df in data.values():
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"data", "quality"}
        assert not df.empty


def test_qc_workflow(local_database, local_dbapi):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres" is available
    fields = [T1S27, T1S33, T1S36, T2S44, T2S46, NEW]
    func = QcFunction(
        "",
        func_name="processGeneric",
        fields=[fields[0]],
        targets=[fields[-1]],
        params={"func": "T1S27 + 5"},
    )

    data = read_stream_data(local_database, streams=fields)

    qc = SaQCWrapper(data)

    qc.execute(func)
    write_qc_data(dbapi=local_dbapi, qc=qc)

    # reloading the data checks that the format is right
    data = read_stream_data(local_database, streams=fields)
    qc = SaQCWrapper(data)


@pytest.mark.parametrize(
    "thing_uuid",
    ("3e23c121-6a6e-48ac-9fb6-9d9a5bf06348", "f3691b96-aca1-4585-95bf-6ea4c611503c"),
)
def test_workflow(thing_uuid, local_database, local_dbapi):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres" is available
    thing = feta.Thing.from_uuid(thing_uuid, dsn=local_database)
    config = thing.project.get_default_qaqc()
    funcs = get_functions(config)
    streams = sum([f.streams for f in funcs], [])

    data = read_stream_data(local_database, streams=streams)
    qc = SaQCWrapper(data)
    for func in funcs:
        qc.execute(func)

    write_qc_data(dbapi=local_dbapi, qc=qc)
