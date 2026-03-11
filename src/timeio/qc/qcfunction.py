#!/usr/bin/env python3
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from timeio.errors import ParsingError
from timeio.qc.utils import StreamInfo

if TYPE_CHECKING:
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


class QcFunction:
    def __init__(
        self,
        name,
        func_name,
        fields: list[StreamInfo],
        params: dict[str, Any],
        targets: list[StreamInfo] | None = None,
        context_window: str | int = 0,
    ):
        self.name = name
        self.func_name: str = func_name
        self.context_window: WindowT = parse_context_window(context_window)
        self.fields = fields
        self.params = params
        self.targets = targets or fields

    def __repr__(self):
        return f"QcFunction({self.name}, func={self.func_name}, params={self.params})"

    @property
    def streams(self) -> list[StreamInfo]:
        return list(set(self.fields + self.targets))

    @property
    def field_names(self) -> list[str]:
        return [f.alias for f in self.fields]

    @property
    def target_names(self) -> list[str]:
        return [f.alias for f in self.targets]


def get_functions(conf: feta.QAQC) -> list[QcFunction]:
    """
    Convert between the database/feta layer and business logic objects
    """

    out = []
    rename_map = {"arg_name": "key"}
    for func in conf.get_tests():
        streams = [
            StreamInfo(**{rename_map.get(k, k): v for k, v in row.items()})
            for row in func.get_streams()
        ]

        qctest = QcFunction(
            name=func.name,
            func_name=func.function,
            fields=[s for s in streams if s.key == "field"],
            targets=[s for s in streams if s.key == "target"],
            params=func.args,
            context_window=conf.context_window,
        )
        out.append(qctest)

    return out


def filter_thing_funcs(funcs: list[QcFunction], thing_id: int) -> list[QcFunction]:
    out = []
    for func in funcs:
        thing_ids = set(int(f.sms_configuration_id) for f in func.fields)
        if thing_id in thing_ids:
            out.append(func)
    return out


def filter_funcs_to_execute(
    all_funcs: list[QcFunction], selected_funcs: list[QcFunction]
):
    to_check = []
    for func in selected_funcs:
        targets = set(t.alias for t in func.targets)
        for target in targets:
            to_check.append(target)

    # build up the function look up table
    lut = {}
    for func in all_funcs:
        fields = set(f.alias for f in func.fields)
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


def filter_functions(funcs: list[QcFunction], thing_id) -> list[QcFunction]:
    thing_funcs = filter_thing_funcs(funcs, thing_id)
    funcs_to_process = filter_funcs_to_execute(funcs, thing_funcs)
    return funcs_to_process
