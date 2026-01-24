#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import typing
from timeio.qc.qctest import QcTest, StreamInfo, Param

if typing.TYPE_CHECKING:
    from timeio import feta

__all__ = [
    "collect_params",
    "collect_tests",
]

logger = logging.getLogger("run-quality-control")


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


def filter_thing_funcs(funcs: list[QcTest], thing_id: int) -> list[QcTest]:
    out = []
    for func in funcs:
        if int(thing_id) in (int(f.thing_id) for f in func.fields):
            out.append(func)
    return out


def collect_tests_to_execute(all_funcs, selected_funcs):

    to_check = []
    for func in selected_funcs:
        for target in func.targets:
            to_check.append(target)

    # build up the function look up table
    lut = {}
    for func in all_funcs:
        for field in func.fields:
            lut[field] = func

    seen = set(selected_funcs)

    # NOTE:
    # we explicitly allow cyclic dependencies, they are resolved in definition order
    # in a setting like
    # func1(field=x, target=y)
    # func2(field=y, target=x)
    # we allow func1 to write y and func2 to overwrite x
    for target in to_check:
        if target in lut:
            func = lut[target]
            to_check.append(func)
            if func not in seen:
                selected_funcs.append(func)

    return selected_funcs


def collect_tests(conf: feta.QAQC, thing: feta.Thing) -> list[QcTest]:
    context_window = conf.context_window

    logging.info(f"THING: {thing}")

    def collect_all_funcs(funcs):
        out = []
        for i, func in enumerate(funcs, start=1):
            try:
                params = collect_params(func)
                qctest = QcTest(
                    name=func.name,
                    func_name=func.function,
                    params=params,
                    context_window=context_window,
                    qctool="saqc",
                )
            except Exception as e:
                e.add_note(f"Qc test {i} ({func})")
                e.add_note(f"Config {conf}")
                raise e
            out.append(qctest)
        return out

    all_funcs = collect_all_funcs(conf.get_tests())
    thing_funcs = filter_thing_funcs(all_funcs, thing.id)
    funcs_to_process = collect_tests_to_execute(all_funcs, thing_funcs)
    return funcs_to_process
