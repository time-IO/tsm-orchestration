from __future__ import annotations

from datetime import datetime
from typing import Any

from timeio.errors import ParsingError
from timeio.parser.mqtt_parser import MqttParser, Observation


class ChirpStackGenericParser(MqttParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        try:
            timestamp = rawdata["time"]
            obj = rawdata["object"]
        except (KeyError, TypeError) as e:
            raise ParsingError(
                "Message must contain the fields 'time' and 'object'"
            ) from e
        if not isinstance(obj, dict):
            raise ParsingError(
                "Field 'object' must be a JSON object (is a payload codec configured?)"
            )
        try:
            datetime.fromisoformat(timestamp)
        except (ValueError, TypeError) as e:
            raise ParsingError(
                f"Invalid 'time' {timestamp!r}, expected an ISO 8601 timestamp"
            ) from e
        out = []
        for key, value in obj.items():
            if key == "Data_time":
                # this is a timestamp, we ignore it
                continue
            try:
                out.append(
                    Observation(
                        timestamp=timestamp,
                        value=value,
                        position=key,
                        origin=origin,
                        header=key,
                    )
                )
            except ValueError:
                self.skip("empty values")
        return out
