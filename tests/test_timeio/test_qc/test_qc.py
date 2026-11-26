#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import json
import random
import sqlite3
import urllib
from unittest.mock import Mock

import pytest
import numpy as np
import pandas as pd

from timeio.databases import Database, DBapi
from timeio.feta import QAQCTest
from timeio.qc import filter_qc_functions
from timeio.qc.qcfunction import (
    QcFunction,
    QcFunctionStream,
    filter_functions_to_execute,
    get_qc_functions,
    merge_qc_streams,
)
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

    def __getattr__(self, name):
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
    "thing_uuid, expected",
    [
        (
            "3e23c121-6a6e-48ac-9fb6-9d9a5bf06348",
            ("Static-T1", "Static-T2", "Static-P1", "Dynamic-P1"),
        ),
        ("f3691b96-aca1-4585-95bf-6ea4c611503c", ("Dynamic-T1", "Dynamic-T2")),
    ],
)
def test_collect_tests(thing_uuid, expected):
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
            params={"function": "(T1S33 + T1S36)/2"},
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

    tests = filter_qc_functions(qc_functions, thing_uuid)
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
                params={"function": "(T1S33 + T1S36) / 2"},
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
        params={"function": "T1S33 + 5"},
    )

    data = read_stream_data(mock_dbapi, streams=[T1S33])
    qc = SaQCWrapper(data)
    qc.execute(func)
    with pytest.raises(ImmutableDatastreamError):
        write_qc_data(dbapi=mock_dbapi, qc=qc)


@pytest.mark.parametrize("dtype", [float, int])
def test_immutable_stream_as_processing_field(mock_dbapi, dtype):
    # processing functions writing to a different target must not
    # count as a modification of their (immutable) field
    target = NEW.to_target()
    func = QcFunction(
        "",
        func_name="processGeneric",
        fields=[T1S33],
        targets=[target],
        params={"function": "T1S33 * 2"},
    )

    data = read_stream_data(mock_dbapi, streams=[T1S33])
    data[T1S33]["data"] = data[T1S33]["data"].astype(dtype)
    qc = SaQCWrapper(data)
    qc.execute(func)
    assert not qc.data_is_modified(T1S33)

    mock_dbapi.insert_datastreams = lambda **kwargs: [{"id": "1"}]
    write_qc_data(dbapi=mock_dbapi, qc=qc)


def test_empty_values_are_not_uploaded(mock_dbapi):
    # resampling data with a gap results in empty (NaN) values,
    # which can't be serialized as JSON
    index = pd.date_range(
        "2025-03-17 00:00", "2025-03-17 09:40", freq="20min", tz="UTC"
    )
    index = index[(index.hour < 3) | (index.hour > 5)]
    data = {T1S33: pd.DataFrame({"data": 1000.0, "quality": None}, index=index)}

    target = NEW.to_target()
    func = QcFunction(
        "",
        func_name="processGeneric",
        fields=[T1S33],
        targets=[target],
        params={"function": "T1S33.resample('1h').mean()"},
    )
    qc = SaQCWrapper(data)
    qc.execute(func)

    uploads = {}

    def upload(name):
        def inner(thing_uuid, **kwargs):
            # requests serializes the payload in the same way
            json.dumps(kwargs, allow_nan=False)
            uploads[name] = next(iter(kwargs.values()))

        return inner

    mock_dbapi.insert_datastreams = lambda **kwargs: [{"id": "1"}]
    mock_dbapi.upsert_observations = upload("observations")
    mock_dbapi.upsert_qc_labels = upload("labels")
    write_qc_data(dbapi=mock_dbapi, qc=qc)

    # 10 hourly bins, 3 of them without data
    assert len(uploads["observations"]) == 7
    assert {o["datastream_pos"] for o in uploads["observations"]} == {"NEW"}


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
        params={"function": "T1S27 + 5"},
    )

    data = read_stream_data(local_dbapi, streams=fields)

    qc = SaQCWrapper(data)

    qc.execute(func)
    write_qc_data(dbapi=local_dbapi, qc=qc)

    # reloading the data checks that the format is right
    data_mod = read_stream_data(local_dbapi, streams=fields)
    qc = SaQCWrapper(data_mod)

    src, trg = data_mod.values()
    assert trg["data"].sort_index().equals(src["data"].sort_index() + 5)


@pytest.mark.parametrize(
    "thing_uuid",
    ("3e23c121-6a6e-48ac-9fb6-9d9a5bf06348", "f3691b96-aca1-4585-95bf-6ea4c611503c"),
)
def test_qc_workflow(thing_uuid, local_database, local_dbapi):
    # NOTE:
    # test only runs if "postgresql://postgres:postgres@localhost/postgres" is available
    thing = feta.Thing.from_uuid(thing_uuid, dsn=local_database)
    config = thing.project.get_default_qaqcs()

    funcs = filter_qc_functions(get_qc_functions(config), thing.id)

    streams = sum([f.streams for f in funcs], [])

    data = read_stream_data(local_dbapi, streams=streams)
    qc = SaQCWrapper(data)
    for func in funcs:
        qc.execute(func)

    write_qc_data(dbapi=local_dbapi, qc=qc)
    # reloading the data checks that the format is right
    data = read_stream_data(local_dbapi, streams=streams)
    qc = SaQCWrapper(data)


def make_stream(alias, thing=1, stream_id=27, context_days=0):
    return QcFunctionStream(
        key="field",
        alias=alias,
        sta_thing_id=thing,
        sta_stream_id=stream_id,
        mutable=False,
        position=alias,
        schema="source",
        datastream_id=stream_id,
        thing_uuid=str(thing),
        context_window=pd.Timedelta(days=context_days),
    )


def make_function(name, field, target):
    return QcFunction(name, "copyField", [field], {}, [target])


@pytest.fixture
def lookup(monkeypatch):
    # Execute the lookup SQL against two deployments of the same property.
    # Only the driver placeholder syntax differs from PostgreSQL.
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        ATTACH DATABASE ':memory:' AS public;
        ATTACH DATABASE ':memory:' AS source;
        CREATE TABLE public.sms_device_mount_action (id, configuration_id);
        CREATE TABLE public.sms_datastream_link (
            device_property_id, device_mount_action_id, datasource_id,
            thing_id, datastream_id, begin_date, end_date
        );
        CREATE TABLE source.datastream (id, position, mutable);
        INSERT INTO public.sms_device_mount_action VALUES (11, 1), (22, 2);
        INSERT INTO public.sms_datastream_link VALUES
            (27, 11, 'source', 'old-thing', 101, NULL, NULL),
            (27, 22, 'source', 'selected-thing', 202, NULL, NULL);
        INSERT INTO source.datastream VALUES
            (101, 'old-position', 0), (202, 'selected-position', 0);
        """)

    def fetchall(conn, query, *params):
        return [dict(row) for row in conn.execute(query.replace("%s", "?"), params)]

    def fetchone(conn, query, *params):
        rows = fetchall(conn, query, *params)
        return rows[0] if rows else None

    qc_test = QAQCTest({}, conn=conn, caching=False)
    monkeypatch.setattr(qc_test, "_fetchall", fetchall)
    monkeypatch.setattr(qc_test, "_fetchone", fetchone)
    yield qc_test, conn
    conn.close()


def test_stream_lookup_uses_selected_thing(lookup):
    qc_test, _ = lookup
    stream = qc_test._get_existing_stream({"sta_stream_id": 27, "sta_thing_id": 2})
    assert stream["thing_uuid"] == "selected-thing"
    assert stream["datastream_id"] == 202
    assert stream["position"] == "selected-position"


def test_stream_lookup_does_not_fall_back_to_another_thing(lookup):
    qc_test, _ = lookup
    with pytest.raises(ValueError, match="does not exist on STA Thing 3"):
        qc_test._get_existing_stream({"sta_stream_id": 27, "sta_thing_id": 3})


def test_stream_lookup_rejects_ambiguous_deployments(lookup):
    qc_test, conn = lookup
    conn.execute(
        "INSERT INTO public.sms_datastream_link VALUES "
        "(27, 22, 'source', 'other-thing', 101, NULL, NULL)"
    )
    with pytest.raises(ValueError, match="multiple deployment links"):
        qc_test._get_existing_stream({"sta_stream_id": 27, "sta_thing_id": 2})


@pytest.mark.parametrize(
    "thing_id,thing_uuid,position,values",
    [
        (1, "old-thing", "old-position", [100.0, 200.0]),
        (2, "selected-thing", "selected-position", [1.0, 2.0]),
    ],
)
def test_selected_deployment_values_reach_saqc(
    lookup, thing_id, thing_uuid, position, values
):
    qc_test, _ = lookup
    meta = qc_test._get_existing_stream({"sta_stream_id": 27, "sta_thing_id": thing_id})
    stream = QcFunctionStream(
        key="field",
        alias="temperature",
        sta_thing_id=thing_id,
        sta_stream_id=27,
        context_window=pd.Timedelta(0),
        start_date=meta.pop("begin_date"),
        **meta,
    )
    index = pd.date_range("2026-01-10", periods=2, tz="UTC")
    deployments = {
        ("old-thing", "old-position"): [100.0, 200.0],
        ("selected-thing", "selected-position"): [1.0, 2.0],
    }

    def observations(uuid, pos, **kwargs):
        return {
            "observations": [
                {
                    "result_time": date.isoformat(),
                    "result_type": 0,
                    "result_number": value,
                    "result_quality": None,
                }
                for date, value in zip(index, deployments[uuid, pos])
            ]
        }

    dbapi = Mock()
    dbapi.get_datastream_observations.side_effect = observations
    qc = SaQCWrapper(read_stream_data(dbapi, [stream], index[0], index[-1]))
    qc.execute(QcFunction("range", "flagRange", [stream], {"max": 10}))

    dbapi.get_datastream_observations.assert_called_once_with(
        thing_uuid, position, start_date=index[0], end_date=index[-1]
    )
    pd.testing.assert_series_equal(
        qc.data[stream]["data"],
        pd.Series(values, index=index, name="data"),
        check_names=False,
        check_freq=False,
    )
    assert [quality["annotation"] for quality in qc.data[stream]["quality"]] == [
        "255.0" if value > 10 else "-inf" for value in values
    ]


def test_dependency_selection_follows_all_branches_and_long_chains():
    x, y, z, w, v = [make_stream(a, i) for i, a in enumerate("xyzwv", 1)]
    first = make_function("first", x, y)
    branch = make_function("branch", y, v)
    second = make_function("second", y, z)
    third = make_function("third", z, w)
    downstream = make_function("downstream", v, v)
    funcs = [first, branch, second, third, downstream]
    assert filter_qc_functions(funcs, "1") == funcs


@pytest.mark.parametrize("branch_first", [False, True])
def test_dependency_chain_uses_fresh_values_and_uploads_all_branches(branch_first):
    x, y, z, w, v, u = [make_stream(a, i) for i, a in enumerate("xyzwvu", 1)]
    for stream in [y, z, w, v]:
        stream.is_mutable = True

    def process(name, field, target, expression):
        return QcFunction(
            name,
            "processGeneric",
            [field],
            {"function": expression},
            [target],
        )

    first = process("first", x, y, "x * 2")
    second = process("second", y, z, "y + 10")
    branch = process("branch", y, v, "y + 100")
    third = process("third", z, w, "z * 3")
    unrelated = process("unrelated", u, u, "u + 1")
    middle = [branch, second] if branch_first else [second, branch]
    funcs = filter_qc_functions([first, *middle, third, unrelated], "1")
    index = pd.date_range("2026-01-10", periods=3, tz="UTC")
    stored = {
        "x": [1.0, 2.0, 3.0],
        "y": [-100.0] * 3,
        "z": [-200.0] * 3,
        "w": [-300.0] * 3,
        "v": [-400.0] * 3,
        "u": [-500.0] * 3,
    }

    def observations(uuid, position, **kwargs):
        return {
            "observations": [
                {
                    "result_time": date.isoformat(),
                    "result_type": 0,
                    "result_number": value,
                    "result_quality": None,
                }
                for date, value in zip(index, stored[position])
            ]
        }

    dbapi = Mock()
    dbapi.get_datastream_observations.side_effect = observations
    streams = [stream for func in funcs for stream in func.streams]
    qc = SaQCWrapper(read_stream_data(dbapi, streams, index[0], index[-1]))
    for func in funcs:
        qc.execute(func)
    write_qc_data(dbapi, qc)

    expected = {
        y: [2.0, 4.0, 6.0],
        z: [12.0, 14.0, 16.0],
        w: [36.0, 42.0, 48.0],
        v: [102.0, 104.0, 106.0],
    }
    for stream, values in expected.items():
        assert qc.data[stream]["data"].tolist() == values
    uploads = {
        call.kwargs["thing_uuid"]: [
            observation["result_number"] for observation in call.kwargs["observations"]
        ]
        for call in dbapi.upsert_observations.call_args_list
    }
    assert uploads == {stream.thing_uuid: values for stream, values in expected.items()}
    assert {
        call.args[1] for call in dbapi.get_datastream_observations.call_args_list
    } == {"x", "y", "z", "w", "v"}


def test_dependency_selection_preserves_order_and_handles_cycles_once():
    x, y, z = [make_stream(a, i) for i, a in enumerate("xyz", 1)]
    first = make_function("first", x, y)
    second = make_function("second", y, x)
    unrelated = make_function("unrelated", z, z)
    selected = [second]
    assert filter_functions_to_execute([first, second, unrelated], selected) == [
        first,
        second,
    ]
    assert selected == [second]


def test_distinct_new_targets_on_same_thing_remain_distinct():
    x, y = [make_stream(a, stream_id=None) for a in "xy"]
    assert x != y
    assert len({x, y}) == 2
    first = make_function("first", make_stream("input"), x)
    unrelated = make_function("unrelated", y, y)
    assert filter_functions_to_execute([first, unrelated], [first]) == [first]


@pytest.mark.parametrize("reverse", [False, True])
def test_shared_stream_uses_longest_context_through_read_execute_write(reverse):
    short = make_stream("temperature", context_days=1)
    long = make_stream("temperature", context_days=7)
    streams = [short, long]
    if reverse:
        streams.reverse()
    start = pd.Timestamp("2026-01-10", tz="UTC")
    end = start + pd.Timedelta(days=1)

    def observations(*args, start_date, end_date):
        return {
            "observations": [
                {
                    "result_time": date.isoformat(),
                    "result_type": 0,
                    "result_number": 10.0,
                    "result_quality": None,
                }
                for date in pd.date_range(start_date, end_date, freq="1D")
            ]
        }

    dbapi = Mock()
    dbapi.get_datastream_observations.side_effect = observations
    data = read_stream_data(dbapi, streams, start, end)
    dbapi.get_datastream_observations.assert_called_once_with(
        "1", "temperature", start_date=start - pd.Timedelta(days=7), end_date=end
    )
    assert next(iter(data.values())).index[0] == start - pd.Timedelta(days=7)
    qc = SaQCWrapper(data)
    for stream in streams:
        qc.execute(QcFunction("range", "flagRange", [stream], {"max": 20}))
    write_qc_data(dbapi, qc)
    labels = dbapi.upsert_qc_labels.call_args.kwargs["qc_labels"]
    assert [row["result_time"] for row in labels] == [
        "2026-01-10T00:00:00.000000Z",
        "2026-01-11T00:00:00.000000Z",
    ]
    dbapi.upsert_observations.assert_not_called()
    assert short.context_window == pd.Timedelta(days=1)
    assert long.context_window == pd.Timedelta(days=7)


def test_function_streams_preserve_context_from_both_fields_and_targets():
    short = make_stream("temperature", context_days=1)
    long = make_stream("temperature", context_days=7)
    func = make_function("range", short, long)
    assert len(func.streams) == 1
    assert func.streams[0].context_window == pd.Timedelta(days=7)


@pytest.mark.parametrize(
    "attribute,value",
    [
        ("sms_configuration_id", 2),
        ("db_stream_id", 99),
        ("thing_uuid", "other-thing"),
        ("start_date", pd.Timestamp("2026-01-01", tz="UTC")),
    ],
)
def test_shared_alias_cannot_silently_replace_a_different_source(attribute, value):
    first = make_stream("temperature")
    other = copy.copy(first)
    setattr(other, attribute, value)
    with pytest.raises(ValueError, match="Conflicting QC sources"):
        merge_qc_streams([first, other])


@pytest.mark.parametrize("processing", [False, True], ids=["flags", "processed-data"])
@pytest.mark.parametrize(
    "timestamps,serialized_timestamps",
    [
        (
            ["2026-01-10T12:00:00+01:00"],
            ["2026-01-10T11:00:00.000000Z"],
        ),
        (
            ["2026-07-10T12:00:00+02:00"],
            ["2026-07-10T10:00:00.000000Z"],
        ),
        (
            ["2026-03-29T01:30:00+01:00", "2026-03-29T03:30:00+02:00"],
            ["2026-03-29T00:30:00.000000Z", "2026-03-29T01:30:00.000000Z"],
        ),
        (
            ["2026-10-25T02:30:00+02:00", "2026-10-25T02:30:00+01:00"],
            ["2026-10-25T00:30:00.000000Z", "2026-10-25T01:30:00.000000Z"],
        ),
        (
            ["2026-07-10T12:00:00.123456+02:00"],
            ["2026-07-10T10:00:00.123456Z"],
        ),
    ],
    ids=["winter", "summer", "dst-start", "dst-end", "microseconds"],
)
def test_qc_upload_timestamps_preserve_instants_and_timezone(
    timestamps, serialized_timestamps, processing
):
    stream = make_stream("temperature")
    stream.is_mutable = processing
    dbapi = Mock()
    dbapi.get_datastream_observations.return_value = {
        "observations": [
            {
                "result_time": timestamp,
                "result_type": 0,
                "result_number": 10.0,
                "result_quality": None,
            }
            for timestamp in timestamps
        ]
    }
    expected = pd.to_datetime(timestamps, utc=True).sort_values()
    data = read_stream_data(dbapi, [stream], expected[0], expected[-1])
    qc = SaQCWrapper(data)
    if processing:
        qc.execute(
            QcFunction(
                "scale", "processGeneric", [stream], {"function": "temperature * 2"}
            )
        )
    qc.execute(QcFunction("range", "flagRange", [stream], {"max": 5}))
    write_qc_data(dbapi, qc)

    labels = dbapi.upsert_qc_labels.call_args.kwargs["qc_labels"]
    payloads = [labels]
    if processing:
        payloads.append(dbapi.upsert_observations.call_args.kwargs["observations"])
    else:
        dbapi.upsert_observations.assert_not_called()

    for payload in payloads:
        assert [row["result_time"] for row in payload] == serialized_timestamps
        assert len(payload) == len(expected)
        for row, original in zip(payload, expected):
            written = pd.Timestamp(row["result_time"])
            # Without an offset the database would interpret this in its own
            # connection timezone, which need not be UTC.
            assert written.tzinfo is not None
            assert written == original
