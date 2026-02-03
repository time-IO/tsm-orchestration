#!/usr/bin/env python3
from __future__ import annotations

import typing
from typing import Any
import pandas as pd

from timeio.errors import ParsingError

if typing.TYPE_CHECKING:
    from timeio import feta
    from timeio.qc.typehints import WindowT

__all__ = ["StreamInfo", "QcFunction"]


def parse_context_window(window: int | str | None) -> WindowT:
    orig = window
    if window is None:
        window = 0

    try:
        if isinstance(window, int) or isinstance(window, str) and window.isnumeric():
            window = int(window)
            is_negative = window < 0
        else:
            window = pd.Timedelta(window)
            is_negative = window.days < 0

        if is_negative:
            raise ValueError("window must not be negative.")

    except Exception as e:
        raise ParsingError(
            f"Parsing context window failed. type={type(orig)}, value={orig}"
        ) from e

    return window


class StreamInfo:
    """Dataclass that stores a stream parameter for a quality test function"""

    def __init__(self, key: str, name: str, thing_id: int, stream_id: int):
        self.key = key
        self.name = name
        self.thing_id = thing_id
        self.stream_id = stream_id
        self.is_immutable = thing_id is not None and stream_id is not None

    def __eq__(self, other):
        if not isinstance(other, StreamInfo):
            return NotImplemented
        return self.thing_id == other.thing_id and self.stream_id == other.stream_id

    def __hash__(self):
        return hash((self.thing_id, self.stream_id))

    def __repr__(self):
        klass = self.__class__.__name__
        return f"{klass}({self.value}, {self.thing_id}, {self.stream_id})"


class QcFunction:
    def __init__(
        self,
        name,
        func_name,
        fields: list[StreamInfo],
        params: dict[str, Any],
        targets: list[StreamInfo] | None,
        context_window: str | int = 0,
    ):
        self.name = name
        self.func_name: str = func_name
        self.context_window: WindowT = parse_context_window(context_window)
        self.fields = fields
        self.params = params
        self.targets = targets or fields

    def __repr__(self):
        return f"QcTest({self.name}, func={self.func_name}, params={self.params})"

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]

    @property
    def target_names(self) -> list[str]:
        return [f.name for f in self.targets]


def get_functions(conf: feta.QAQC) -> list[QcFunction]:
    """
    Convert between the database/feta layer and business logic objects
    """

    def get_func_fields(test: feta.QAQCTest):
        out = []
        for stream in test.streams or []:
            if stream["arg_name"] == "field":
                out.append(
                    StreamInfo(
                        stream["arg_name"],
                        stream["alias"],
                        stream["sta_thing_id"],
                        stream["sta_stream_id"],
                    )
                )
        return out

    def get_func_targets(test: feta.QAQCTest):
        out = []
        for stream in test.streams or []:
            if stream["arg_name"] == "target":
                out.append(
                    StreamInfo(
                        stream["arg_name"],
                        stream["alias"],
                        stream["sta_thing_id"],
                        stream["sta_stream_id"],
                    )
                )
        return out

    out = []
    for i, func in enumerate(conf.get_tests(), start=1):
        try:
            qctest = QcFunction(
                name=func.name,
                func_name=func.function,
                fields=get_func_fields(func),
                targets=get_func_targets(func),
                params=func.args,
                context_window=conf.context_window,
            )
        except Exception as e:
            e.add_note(f"Qc test {i} ({func})")
            e.add_note(f"Config {conf}")
            raise e
        out.append(qctest)

    return out


def filter_thing_funcs(funcs: list[QcFunction], thing_id: int) -> list[QcFunction]:
    out = []
    for func in funcs:
        thing_ids = set(int(f.thing_id) for f in func.fields)
        if thing_id in thing_ids:
            out.append(func)
    return out


def filter_funcs_to_execute(
    all_funcs: list[QcFunction], selected_funcs: list[QcFunction]
):

    to_check = []
    for func in selected_funcs:
        targets = set(t.name for t in func.targets)
        for target in targets:
            to_check.append(target)

    # build up the function look up table
    lut = {}
    for func in all_funcs:
        fields = set(f.name for f in func.fields)
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


def get_functions_to_execute(funcs: list[QcFunction], thing_id) -> list[QcFunction]:

    thing_funcs = filter_thing_funcs(funcs, thing_id)
    funcs_to_process = filter_funcs_to_execute(funcs, thing_funcs)
    return funcs_to_process
