from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from timeio.typehints import TimestampT
from timeio.parser.typehints import ObservationPayloadT

parsedT = TypeVar("parsedT")


class AbcParser(ABC):
    def __init__(self):
        self._start_date: TimestampT | None = None
        self._end_date: TimestampT | None = None

    @abstractmethod
    def do_parse(self, *args) -> parsedT:
        raise NotImplementedError

    @abstractmethod
    def to_observations(self, *args) -> list[ObservationPayloadT]:
        raise NotImplementedError

    @property
    def start_date(self) -> str | None:
        if self._start_date is not None:
            return self._start_date.isoformat()

    @property
    def end_date(self) -> str | None:
        if self._end_date is not None:
            return self._end_date.isoformat()
