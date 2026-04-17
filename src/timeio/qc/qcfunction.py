#!/usr/bin/env python3
from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

if TYPE_CHECKING:
    from timeio import feta
    from timeio.typehints import TimestampT


class QcFunctionStream:
    """Dataclass that stores a stream parameter for a quality test function
    stream_id and thing_id are definied as SMS entities with
    - stream_id -> device_propert_id
    - thing_id  -> configuration_id
    """

    def __init__(
        self,
        key: Literal["field", "target"],
        alias: str,
        sta_thing_id: int,
        sta_stream_id: int | None,
        mutable: bool,
        position: str,
        schema: str,
        datastream_id: int | None,
        thing_uuid: str,
        context_window: pd.Timedelta,
        start_date: TimestampT | None = None,
        end_date: TimestampT | None = None,
    ):
        # TODO: improve attribute names
        self.key = key
        self.alias: str = alias
        self.sms_configuration_id = sta_thing_id
        self.sta_stream_id = sta_stream_id
        self.datastream_name: str = alias
        self.db_schema = schema
        self.db_stream_id = datastream_id
        self.thing_uuid = thing_uuid
        self.position = position
        self.is_mutable = mutable
        self.context_window = context_window
        # we store the data linking start and end date to allow
        # queries against the observation instead of OBSERVATIONS
        self.start_date = start_date
        self.end_date = end_date

    def to_target(self):
        out = copy.deepcopy(self)
        out.key = "target"
        return out

    def __eq__(self, other):
        if not isinstance(other, QcFunctionStream):
            return NotImplemented
        return (
            self.sms_configuration_id == other.sms_configuration_id
            and self.sta_stream_id == other.sta_stream_id
        )

    def __hash__(self):
        return hash((self.alias, self.sms_configuration_id, self.sta_stream_id))

    def __repr__(self):
        klass = self.__class__.__name__
        return f"{klass}({self.key}, {self.alias})"


class QcFunction:
    def __init__(
        self,
        name,
        func_name,
        fields: list[QcFunctionStream],
        params: dict[str, Any],
        targets: list[QcFunctionStream] | None = None,
    ):
        self.name = name
        self.func_name: str = func_name
        self.fields = fields
        self.params = params
        self.targets = targets or [f.to_target() for f in fields]

    def __repr__(self):
        return f"QcFunction({self.name}, field={self.field_names}, target={self.target_names}, func={self.func_name}, params={self.params})"

    @property
    def streams(self) -> list[QcFunctionStream]:
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
    rename_map = {"arg_name": "key", "begin_date": "start_date"}
    for func in conf.get_tests():

        streams = [
            QcFunctionStream(**{rename_map.get(k, k): v for k, v in stream.items()})
            for stream in func.get_streams()
        ]

        qctest = QcFunction(
            name=func.name,
            func_name=func.function,
            fields=[s for s in streams if s.key == "field"],
            targets=[s for s in streams if s.key == "target"],
            params=func.args,
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
) -> list[QcFunction]:
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


def filter_functions(funcs: list[QcFunction], sta_thing_id) -> list[QcFunction]:
    thing_funcs = filter_thing_funcs(funcs, sta_thing_id)
    funcs_to_process = filter_funcs_to_execute(funcs, thing_funcs)
    return funcs_to_process
