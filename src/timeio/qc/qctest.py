#!/usr/bin/env python3
import pandas as pd
from typing import Any
from timeio import feta
from timeio.errors import UserInputError
from .qctools import QcTool


class Param:
    def __init__(self, name, value: Any, *args):
        self.name = name
        self.value = value

    def parse(self):
        # cast according to Datatype
        return self.value


class StreamParam(Param):
    def __init__(self, name, value: Any, thing_id, stream_id, *args):
        super().__init__(name, value, StreamParam)
        self.stream_id = stream_id
        self.thing_id = thing_id
        # todo: add alias parsing

    def parse(self):
        # cast according to Datatype
        return self.value


class QcTest:
    def __init__(self, name, func_name, params: list[Param], context_window=None):
        self.func_name = func_name
        self._params = params
        self._window = context_window

        # filled by QcTest.parse()
        self.name = name or "Unnamed QcTest"
        self.context_window = None
        self.args = {}
        self.streams: list[StreamParam] = []

    @classmethod
    def from_feta(cls, test: feta.QAQCTest):
        params = []
        for stream in test.streams or []:  # type: feta.QcStreamT
            params.append(
                StreamParam(
                    stream["arg_name"],
                    stream["sta_thing_id"],
                    stream["sta_stream_id"],
                    stream["alias"],
                )
            )
        for key, value in test.args.items():
            params.append(Param(key, value))
        return cls(test.name, test.function, params)

    def parse(self, qctool: QcTool):
        self._parse_window()
        qctool.check_func_name(self.func_name)
        for p in self._params:
            self.args[p.name] = p.parse()
            if isinstance(p, StreamParam):
                self.streams.append(p)

    def _parse_window(self):
        window = self._window
        if window is None:
            window = 0
        if isinstance(window, int) or isinstance(window, str) and window.isnumeric():
            window = int(window)
            is_negative = window < 0
        else:
            window = pd.Timedelta(window)
            is_negative = window.days < 0

        if is_negative:
            raise UserInputError(
                "Parameter 'context_window' must not have a negative value"
            )
        self.context_window = window
