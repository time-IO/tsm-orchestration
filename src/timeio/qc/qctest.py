#!/usr/bin/env python3
from __future__ import annotations

import logging
import typing
from typing import Any

import pandas as pd

from timeio.errors import UserInputError
from timeio.qc.qctools import QcTool, get_qctool

__all__ = ["Param", "StreamInfo", "QcTest", "QcResult"]

if typing.TYPE_CHECKING:
    from timeio.qc.stream_manager import StreamManager
    from timeio.qc.typeshints import WindowT, TimestampT


def parse_context_window(window: int | str | None) -> WindowT:
    if window is None:
        window = 0
    if isinstance(window, int) or isinstance(window, str) and window.isnumeric():
        window = int(window)
        is_negative = window < 0
    else:
        window = pd.Timedelta(window)
        is_negative = window.days < 0

    if is_negative:
        raise ValueError("window must not be negative.")

    return window


class Param:
    """Dataclass that stores a parameter for a quality test function"""

    def __init__(self, key, value: Any, *args):
        self.key = key
        self.value = value

    def parse(self):
        # cast according to Datatype
        return self.value


class StreamInfo(Param):
    """Dataclass that stores a stream parameter for a quality test function"""

    def __init__(self, key, value: Any, thing_id, stream_id):
        super().__init__(key, value)
        self.thing_id = thing_id
        self.stream_id = stream_id

        self.is_immutable = thing_id is not None and stream_id is not None
        self.is_dataproduct = thing_id is not None and stream_id is None
        self.is_temporary = thing_id is None  # and stream_id is dont-care

    def parse(self):
        # cast according to Datatype
        return self.value

    def __repr__(self):
        klass = self.__class__.__name__
        return f"{klass}({self.value}, {self.thing_id}, {self.stream_id})"


class QcResult:
    """Simple dataclass to store the result of QcTest.run()"""

    columns: list[str] | pd.Index
    data: dict[str, pd.Series]
    quality: dict[str, pd.Series]
    origin: str


class QcTest:
    def __init__(
        self,
        name,
        func_name,
        params: list[Param],
        context_window: str | int,
        qctool: str | QcTool,
    ):
        self.name = name or "Unnamed QcTest"
        self.func_name = func_name
        self.params = params
        self.streams = [p for p in self.params if isinstance(p, StreamInfo)]
        self.context_window = context_window
        self.result: QcResult | None = None

        if isinstance(qctool, str):
            qctool = get_qctool(qctool)
        self._qctool: QcTool = qctool()

        # filled by QcTest.parse()
        self._parsed_window = None
        self._parsed_args = {}

    def __repr__(self):
        return f"QcTest({self.name}, func={self.func_name})"

    def parse(self):
        self._qctool.check_func_name(self.func_name)
        try:
            self._parsed_window = parse_context_window(self.context_window)
        except ValueError:
            raise UserInputError(
                "Parameter 'context_window' must not have a negative value"
            )
        for p in self.params:
            self._parsed_args[p.key] = p.parse()

    def load_data(
        self,
        sm: StreamManager,
        start_date: TimestampT | None = None,
        end_date: TimestampT | None = None,
    ):
        window = self._parsed_window
        if window is None:
            raise RuntimeError("Must call QcTest.parse before load_data.")
        data = {}
        qual = {}
        for stream_info in self.streams:
            name = stream_info.value
            if name in data:
                continue

            stream = sm.get_stream(stream_info)

            if start_date is None:
                start_date, end_date = stream.get_unprocessed_range()

            df = stream.get_data(start_date, end_date, window)
            data[name] = df["data"]
            qual[name] = df["quality"]

        self._qctool.add_data(data, qual)

    def run(self) -> None:
        func = self.func_name
        kws = self._parsed_args
        logging.debug(
            "executing tool: %s, func: %s,  kwargs: %s", self._qctool.name, func, kws
        )
        self._qctool.execute(func, **kws)

        self.result = QcResult()
        self.result.data = self._qctool.get_data()
        self.result.quality = self._qctool.get_quality()
        self.result.columns = pd.Index(self.result.quality.keys())
        self.result.origin = repr(self)
