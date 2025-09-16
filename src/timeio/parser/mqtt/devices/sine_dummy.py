from __future__ import annotations

from typing import Any
import datetime

from timeio.parser.mqtt.parser import MqttParser, Observation


class SineDummyParser(MqttParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        timestamp = datetime.now()
        return [
            Observation(
                timestamp=timestamp,
                value=rawdata["sine"],
                position=0,
                origin=origin,
                header="sine",
            ),
            Observation(
                timestamp=timestamp,
                value=rawdata["cosine"],
                position=1,
                origin=origin,
                header="cosine",
            ),
        ]
