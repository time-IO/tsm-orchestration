from __future__ import annotations

from typing import Any

from timeio.parser.abc_parser import AbcParser
from timeio.parser.pandas_parser import PandasParser
from timeio.parser.csv_parser import CsvParser
from timeio.parser.json_parser import JsonParser
from timeio.parser.soilcan_parser import SoilcanParser
from timeio.parser.mqtt_parser import MqttParser
from timeio.parser.mqtt_devices.campbell_cr6 import CampbellCr6Parser
from timeio.parser.mqtt_devices.chirpstack_generic import ChirpStackGenericParser
from timeio.parser.mqtt_devices.ydoc_ml_417 import YdocMl417Parser
from timeio.parser.mqtt_devices.quaesta import QuaestaParser

_parser_map = {
    "csv": CsvParser,
    "json": JsonParser,
    "soilcan": SoilcanParser,
    # MQTT
    "campbell_cr6": CampbellCr6Parser,
    "ydoc_ml417": YdocMl417Parser,
    "chirpstack_generic": ChirpStackGenericParser,
    "quaesta": QuaestaParser,
}


def get_parser(
    parser_type: str, settings: dict[str, Any] | None
) -> CsvParser | JsonParser | MqttParser | SoilcanParser:
    """Get initialized parser by name."""

    klass = _parser_map.get(parser_type)
    if klass is None:
        raise NotImplementedError(f"parser {parser_type!r} not known")

    if issubclass(klass, PandasParser):
        return klass(settings or {})

    return klass()
