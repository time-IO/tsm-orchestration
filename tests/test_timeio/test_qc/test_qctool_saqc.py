#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from datetime import datetime

import pandas as pd

from timeio.databases import Database
from timeio.qc import get_functions_to_execute
from timeio.qc.qctest import QcTest, StreamInfo
from timeio.qc.utils import load_data
from timeio.qc.saqc import init_saqc, execute_qc_function


def select_thing_by_name(things, thing_name):
    return [t for t in things if t.name == thing_name][0]


@pytest.fixture()
def qc_functions():
    return [
        QcTest(
            "Static-T1",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo(key="field", value="T1S33", thing_id=1, stream_id=33)],
            targets=[StreamInfo(key="target", value="T1S33", thing_id=1, stream_id=33)],
            params={"min": 900, "max": 1200}
        ),
        QcTest(
            "Static-T2",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo("field", "T1S36", 1, 36)],
            targets=[StreamInfo("target", "T1S36", 1, 36)],
            params={"min": 900, "max": 1200}
        ),
        QcTest(
            "Static-P1",
            context_window=0,
            func_name="processGeneric",
            fields=[StreamInfo("field", "T1S33", 1, 33), StreamInfo("field", "T1S36", 1, 36)],
            targets=[StreamInfo("target", "T1S33", 1, 33), StreamInfo("target", "T1S36", 1, 36)],
            params={"func": "lambda x, y: (x + y)/2"}
        ),
        QcTest(
            "Dynamic-T1",
            context_window=0,
            func_name="flagRange",
            fields=[StreamInfo("field", "T2S44", 4, 44)],
            targets=[StreamInfo("target", "T2S44", 4, 44)],
            params={"min": 0, "max": 15}
        ),
        # QcTest(
        #     "Dynamic-T2",
        #     context_window=0,
        #     func_name="flagUniLOF",
        #     fields=[StreamInfo("field", "T2S46", 4, 46)],
        #     targets=[StreamInfo("target", "T2S46", 4, 46)],
        #     params={}
        # ),
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

def test_data_loading(qc_functions):

    fields = []
    for f in qc_functions:
        fields.extend(f.fields)

    dsn = "postgresql://postgres:postgres@localhost/postgres"
    with Database(dsn).connection() as conn:
        data = load_data(conn, streams=fields)


def test_function_execution(qc_functions):

    fields = []
    for f in qc_functions:
        fields.extend(f.fields)

    dsn = "postgresql://postgres:postgres@localhost/postgres"
    with Database(dsn).connection() as conn:
        data = load_data(conn, streams=fields)


    qc = init_saqc(data)
    for func in qc_functions:
        print(func)
        qc = execute_qc_function(qc, func)
