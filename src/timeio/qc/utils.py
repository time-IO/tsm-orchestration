#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import annotations

import logging

from timeio import feta
from timeio.qc.qctest import QcTest, StreamInfo, Param

logger = logging.getLogger(__name__)


def collect_params(test: feta.QAQCTest):
    params = []
    for stream in test.streams or []:
        params.append(
            StreamInfo(
                stream["arg_name"],
                stream["alias"],
                stream["sta_thing_id"],
                stream["sta_stream_id"],
            )
        )
    for key, value in test.args.items():
        params.append(Param(key, value))
    return params


def collect_tests(conf: feta.QAQC) -> list[QcTest]:
    context_window = conf.context_window
    tests = []
    for i, test in enumerate(conf.get_tests()):  # type: int, feta.QAQCTest
        params = collect_params(test)
        qctest = QcTest(
            name=test.name,
            func_name=test.function,
            params=params,
            context_window=context_window,
            qctool="saqc",
        )
        tests.append(qctest)
    return tests
