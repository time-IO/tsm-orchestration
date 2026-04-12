#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import urllib

import pytest
import numpy as np
import pandas as pd

from timeio.databases import Database, DBapi
from timeio.qc import filter_functions
from timeio.qc.qcfunction import QcFunction, QcFunctionStream, get_functions
from timeio.qc.io import read_stream_data, write_qc_data, ImmutableDatastreamError
from timeio.qc.saqc import SaQCWrapper
from timeio import feta

T1S27 = QcFunctionStream(
    key="field",
    alias="T1S27",
    sta_thing_id=1,
    sta_stream_id=27,
    mutable=False,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="3e23c121-6a6e-48ac-9fb6-9d9a5bf06348",
    datastream_id=15,
    context_window=pd.Timedelta(days=5),
    position="N1Cts",
)
T1S33 = QcFunctionStream(
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
T1S36 = QcFunctionStream(
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
T2S44 = QcFunctionStream(
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
T2S43 = QcFunctionStream(
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
T2S46 = QcFunctionStream(
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
NEW = QcFunctionStream(
    key="field",
    alias="NEW",
    sta_thing_id=2,
    sta_stream_id=None,
    mutable=True,
    schema="vo_demogroup_887a7030491444e0aee126fbc215e9f7",
    thing_uuid="f3691b96-aca1-4585-95bf-6ea4c611503c",
    datastream_id=None,
    context_window=pd.Timedelta(0),
    position="NEW",
)


class MockDBapi:
    def get_datastream_observations(
        self, *args, start_date=None, end_date=None, **kwargs
    ):
        out = []
        for date in pd.date_range(start_date, end_date, periods=10):
            out.append(
                {
                    "result_time": date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "result_type": 0,
                    "result_number": random.uniform(10, 500),
                    "result_quality": None,
                }
            )

        return {"observations": out}

    def upsert_qc_labels(self, thing_uuid, qc_labels):
        dates = sorted([pd.Timestamp(d["result_time"]) for d in qc_labels])
        import ipdb

        ipdb.set_trace()
        pass

    def __getattr__(self, name):
        print("NAME:", name)
        return lambda *args, **kwargs: None


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
    url = "http://localhost:8001"
    token = "local_bearer_token_processing"
    try:
        return DBapi(base_url=url, auth_token=token)
    except urllib.error.URLError:
        pytest.skip("local dbapi connection not available")


@pytest.fixture()
def mock_dbapi():
    return MockDBapi()


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


def test_mutable_stream_overwrite(mock_dbapi):
    # 1. create a mutable datastream
    func = QcFunction(
        "",
        func_name="copyField",
        fields=[T2S43],
        targets=[NEW],
        params={"overwrite": "True"},
    )

    data = read_stream_data(mock_dbapi, streams=[T2S43, NEW.to_target()])
    qc = SaQCWrapper(data)
    qc.execute(func)
    s1, s2 = qc.data.values()
    assert s1.equals(s2)


def test_immutable_stream_overwrite(mock_dbapi):
    func = QcFunction(
        "",
        func_name="processGeneric",
        fields=[T1S33],
        params={"func": "T1S33 + 5"},
    )

    data = read_stream_data(mock_dbapi, streams=[T1S33])
    qc = SaQCWrapper(data)
    qc.execute(func)
    with pytest.raises(ImmutableDatastreamError):
        write_qc_data(dbapi=mock_dbapi, qc=qc)


def test_context_window(mock_dbapi):
    start_date = pd.Timestamp("2021-03-06", tz="UTC")
    data = read_stream_data(
        mock_dbapi,
        streams=[T1S27],
        start_date=start_date,
        end_date=start_date + pd.Timedelta(days=10),
    )
    assert data[T1S27].index[0] == start_date - T1S27.context_window

def test_db_data_reading(local_dbapi):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres" is available
    fields = [T1S27, T1S33, T1S36, T2S44, T2S46]

    data = read_stream_data(local_dbapi, streams=fields)

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


def test_processing_workflow(local_dbapi):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres" is available
    fields = [T1S27, NEW]
    func = QcFunction(
        "",
        func_name="processGeneric",
        fields=[T1S27],
        targets=[NEW],
        params={"func": "T1S27 + 5"},
    )

    data = read_stream_data(local_dbapi, streams=fields)

    qc = SaQCWrapper(data)

    qc.execute(func)
    write_qc_data(dbapi=local_dbapi, qc=qc)

    # reloading the data checks that the format is right
    data_mod = read_stream_data(local_dbapi, streams=fields)
    qc = SaQCWrapper(data_mod)

    src, trg = data_mod.values()
    assert trg.sort_index().equals(src.sort_index() + 5)


@pytest.mark.parametrize(
    "thing_uuid",
    ("3e23c121-6a6e-48ac-9fb6-9d9a5bf06348", "f3691b96-aca1-4585-95bf-6ea4c611503c"),
)
def test_qc_workflow(thing_uuid, local_database, local_dbapi):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres" is available
    thing = feta.Thing.from_uuid(thing_uuid, dsn=local_database)
    config = thing.project.get_default_qaqc()

    funcs = filter_functions(get_functions(config), thing.id)

    streams = sum([f.streams for f in funcs], [])

    data = read_stream_data(local_dbapi, streams=streams)
    qc = SaQCWrapper(data)
    for func in funcs:
        qc.execute(func)

    write_qc_data(dbapi=local_dbapi, qc=qc)
    # reloading the data checks that the format is right
    data = read_stream_data(local_dbapi, streams=streams)
    qc = SaQCWrapper(data)
