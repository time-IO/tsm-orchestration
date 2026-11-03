from __future__ import annotations

from typing import Any

from timeio.errors import ParsingError
from timeio.parser.mqtt_parser import MqttParser, Observation


class CampbellCr6Parser(MqttParser):
    # the basic data massage looked like this
    # {
    #     "type": "Feature",
    #     "geometry": {"type": "Point", "coordinates": [null, null, null]},
    #     "properties": {
    #         "loggerID": "CR6_18341",
    #         "observationNames": ["Batt_volt_Min", "PTemp"],
    #         "observations": {"2022-05-24T08:53:00Z": [11.9, 26.91]}
    #     }
    # }

    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        if not isinstance(rawdata, dict):
            raise ParsingError("Message must be a JSON object")
        properties = rawdata.get("properties")
        if properties is None:
            return self.ignore("message has no 'properties'")

        try:
            names = properties["observationNames"]
            observations = properties["observations"].items()
        except (KeyError, TypeError, AttributeError) as e:
            raise ParsingError(
                "Message must contain 'properties.observationNames' "
                "and 'properties.observations'"
            ) from e
        if not isinstance(names, list):
            raise ParsingError("Field 'properties.observationNames' must be a list")

        out = []
        for timestamp, values in observations:
            if not isinstance(values, list):
                raise ParsingError(
                    f"Observations at {timestamp!r} must be a list of values"
                )
            if len(values) > len(names):
                self.skip("values without name", len(values) - len(names))
            elif len(values) < len(names):
                self.skip("missing values", len(names) - len(values))
            for i, (key, value) in enumerate(zip(names, values)):
                try:
                    out.append(
                        Observation(
                            timestamp=timestamp,
                            value=value,
                            position=i,
                            origin=origin,
                            header=key,
                        )
                    )
                except ValueError:
                    self.skip("empty values")
        return out
