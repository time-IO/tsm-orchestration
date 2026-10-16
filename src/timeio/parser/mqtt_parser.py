from __future__ import annotations

import json
import logging
import math

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from timeio.parser.abc_parser import AbcParser
from timeio.journaling import Journal
from timeio.common import ObservationResultType
from timeio.parser.typehints import ObservationPayloadT

journal = Journal("MqttParser", errors="warn")


@dataclass
class Observation:
    # This is a legacy class of the datastore_lib
    # see tsm_datastore_lib.Observation
    timestamp: datetime | str
    value: float | int | str | bool
    origin: str
    position: int
    header: str = ""

    def __post_init__(self):
        if self.value is None:
            raise ValueError("None is not allowed as observation value.")
        if isinstance(self.value, float) and math.isnan(self.value):
            raise ValueError("NaN is not allowed as observation value.")


class MqttParser(AbcParser):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self._start_date = None
        self._end_date = None

    @abstractmethod
    def do_parse(self, rawdata: Any, origin: str) -> list[Observation]:
        raise NotImplementedError

    def to_observations(
        self, data: list[Observation], thing_uuid: str
    ) -> list[ObservationPayloadT]:
        result = []
        timestamps = []
        for ob in data:
            if isinstance(ts := ob.timestamp, datetime):
                ts = ts.isoformat()
            obpay: ObservationPayloadT = {
                "result_type": -99999,  # dummy value
                "result_time": str(ts),
                "datastream_pos": str(ob.position),
                "parameters": json.dumps(
                    {
                        "origin": ob.origin,
                        "column_header": ob.header,
                    }
                ),
            }
            if isinstance(ob.value, bool):
                obpay["result_boolean"] = ob.value  # noqa
                obpay["result_type"] = ObservationResultType.Bool
            elif isinstance(ob.value, (float, int)):
                obpay["result_number"] = ob.value
                obpay["result_type"] = ObservationResultType.Number
            elif isinstance(ob.value, str):
                obpay["result_string"] = ob.value
                obpay["result_type"] = ObservationResultType.String
            elif isinstance(ob.value, dict):
                obpay["result_json"] = json.dumps(ob.value)
                obpay["result_type"] = ObservationResultType.Json
            else:
                journal.warning(
                    f"Data of type {type(ob.value).__name__} is "
                    f"not supported. Failing Observation: {ob}",
                    thing_uuid,
                )
                continue
            result.append(obpay)
            timestamps.append(ob.timestamp)

        self._set_date_range(timestamps, thing_uuid)
        return result

    def _set_date_range(self, timestamps: list[datetime | str], thing_uuid: str):
        """Set start and end date from the timestamps of the emitted observations.

        Leaves both dates unset if there are no timestamps or they cannot be
        compared (unparsable strings, mixed naive and aware timestamps).
        """
        self._start_date = self._end_date = None
        if not timestamps:
            return
        try:
            parsed = [pd.Timestamp(ts) for ts in timestamps]
            if any(pd.isna(ts) for ts in parsed):
                raise ValueError("empty timestamp")
            self._start_date, self._end_date = min(parsed), max(parsed)
        except (ValueError, TypeError) as e:
            self.logger.warning(
                f"Could not determine time range of thing {thing_uuid}: {e}"
            )
