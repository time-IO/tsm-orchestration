#!/usr/bin/env python3
from __future__ import annotations

import copy
from collections import defaultdict
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
            self.alias == other.alias
            and self.sms_configuration_id == other.sms_configuration_id
            and self.sta_stream_id == other.sta_stream_id
        )

    def __hash__(self):
        return hash((self.alias, self.sms_configuration_id, self.sta_stream_id))

    def __repr__(self):
        klass = self.__class__.__name__
        return f"{klass}({self.key}, {self.alias})"


def merge_qc_streams(streams: list[QcFunctionStream]) -> list[QcFunctionStream]:
    """Merge shared aliases without losing history or hiding conflicting sources."""
    merged = {}
    source_attributes = (
        "sms_configuration_id",
        "sta_stream_id",
        "db_schema",
        "db_stream_id",
        "thing_uuid",
        "position",
        "is_mutable",
        "start_date",
        "end_date",
    )
    for stream in streams:
        if stream.alias not in merged:
            merged[stream.alias] = copy.copy(stream)
            continue
        existing = merged[stream.alias]
        if any(
            getattr(existing, attr) != getattr(stream, attr)
            for attr in source_attributes
        ):
            raise ValueError(f"Conflicting QC sources for alias '{stream.alias}'")
        # Different QC settings can request different amounts of history for the
        # same stream. Keep the largest window so every function gets enough
        # preceding observations; keeping the first request could truncate history.
        existing.context_window = max(existing.context_window, stream.context_window)
    return list(merged.values())


class QcFunction:
    def __init__(
        self,
        name,
        func_name,
        fields: list[QcFunctionStream],
        params: dict[str, Any],
        targets: list[QcFunctionStream] | None = None,
        setting_name: str | None = None,
    ):
        self.name = name
        self.func_name: str = func_name
        self.fields = fields
        self.params = params
        self.targets = targets or [f.to_target() for f in fields]
        self.setting_name = setting_name

    def __repr__(self):
        return f"QcFunction({self.name}, field={self.field_names}, target={self.target_names}, func={self.func_name}, params={self.params})"

    @property
    def streams(self) -> list[QcFunctionStream]:
        return merge_qc_streams(self.fields + self.targets)

    @property
    def field_names(self) -> list[str]:
        return [f.alias for f in self.fields]

    @property
    def target_names(self) -> list[str]:
        return [f.alias for f in self.targets]


def get_qc_functions(qc_settings: list[feta.QAQC]) -> list[QcFunction]:
    """
    Convert between the database/feta layer and business logic objects
    """
    out = []
    rename_map = {"arg_name": "key", "begin_date": "start_date"}
    for setting in qc_settings:
        for func in setting.get_functions():
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
                setting_name=setting.name,
            )
            out.append(qctest)
    return out


def get_qc_things(funcs: list[QcFunction]) -> list[str]:
    uuids = set()
    for func in funcs:
        for stream in func.streams:
            uuids.add(stream.thing_uuid)
    return list(uuids)


def filter_thing_functions(
    funcs: list[QcFunction], thing_uuid: str
) -> list[QcFunction]:
    out = []
    for func in funcs:
        uuids = set(str(f.thing_uuid) for f in func.fields)
        if thing_uuid in uuids:
            out.append(func)
    return out


def filter_functions_to_execute(
    all_funcs: list[QcFunction], selected_funcs: list[QcFunction]
) -> list[QcFunction]:
    consumers = defaultdict(list)
    for func in all_funcs:
        for field in func.fields:
            consumers[field].append(func)

    to_check = list(selected_funcs)
    seen = set(selected_funcs)
    for func in to_check:
        for target in func.targets:
            for consumer in consumers[target]:
                if consumer not in seen:
                    seen.add(consumer)
                    to_check.append(consumer)

    # Cycles are allowed; execute each selected function once, in definition order.
    return [func for func in all_funcs if func in seen]


def filter_qc_functions(funcs: list[QcFunction], thing_uuid: str) -> list[QcFunction]:
    thing_funcs = filter_thing_functions(funcs, thing_uuid)
    funcs_to_process = filter_functions_to_execute(funcs, thing_funcs)
    return funcs_to_process
