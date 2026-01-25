#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import typing
from timeio.qc.qctest import QcTest, StreamInfo, Param

if typing.TYPE_CHECKING:
    from timeio import feta

__all__ = [
    "get_qc_functions_to_execute",
    "get_qc_functions"
]

logger = logging.getLogger("run-quality-control")


def get_func_arguments(test: feta.QAQCTest):
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


def get_qc_functions(conf: feta.QAQC) -> list[QcTest]:
    """
    Convert between the database/feta layer and business logic objects
    """
    out = []
    context_window = conf.context_window
    for i, func in enumerate(conf.get_tests(), start=1):
        try:
            params = get_func_arguments(func)
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


def filter_thing_funcs(funcs: list[QcTest], thing_id: int) -> list[QcTest]:
    out = []
    for func in funcs:
        thing_ids = set(int(s.thing_id) for s in func.get_streams_by_key("field"))
        if thing_id in thing_ids:
            out.append(func)
    return out


def filter_funcs_to_execute(all_funcs, selected_funcs):

    to_check = []
    for func in selected_funcs:
        targets = set(s.value for s in func.get_streams_by_key("target"))
        for target in targets:
            to_check.append(target)

    # build up the function look up table
    lut = {}
    for func in all_funcs:
        fields = set(s.value for s in func.get_streams_by_key("field"))
        for field in fields:
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


def get_qc_functions_to_execute(funcs: list[QcTest], thing_id) -> list[QcTest]:

    thing_funcs = filter_thing_funcs(funcs, thing_id)
    funcs_to_process = filter_funcs_to_execute(funcs, thing_funcs)
    return funcs_to_process
