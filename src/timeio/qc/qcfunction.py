#!/usr/bin/env python3
from __future__ import annotations

import typing
from typing import Any
import pandas as pd

from timeio.errors import ParsingError

if typing.TYPE_CHECKING:
    from timeio.qc.typeshints import WindowT

__all__ = ["StreamInfo", "QcFunction", "QcResult"]



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

    # TODO: Remove dependency on Param (and Param, if possible)

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


class QcResult:
    """Simple dataclass to store the result of QcTest.run()"""

    columns: list[str] | pd.Index
    data: dict[str, pd.Series]
    quality: dict[str, pd.Series]
    origin: str


class QcFunction:
    # TODO:
    # - rename to QcFunction
    # - make targets optional
    def __init__(
        self,
        name,
        func_name,
        fields: list[StreamInfo],
        targets: list[StreamInfo],
        params: dict[str, Any],
        context_window: str | int,
    ):
        self.name = name
        self.func_name: str = func_name
        self.context_window: WindowT = parse_context_window(context_window)
        self.fields = fields
        self.targets = targets
        self.params = params

    def __repr__(self):
        return f"QcTest({self.name}, func={self.func_name}, params={self.params})"

    @property
    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]

    @property
    def target_names(self) -> list[str]:
        return [f.name for f in self.targets]
