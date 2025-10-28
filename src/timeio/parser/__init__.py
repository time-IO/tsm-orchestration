from __future__ import annotations

from timeio.parser.abc_parser import AbcParser
from timeio.parser.pandas_parser import PandasParser
from timeio.parser.csv_parser import CsvParser
from timeio.parser.json_parser import JsonParser
from timeio.parser.mqtt_parser import MqttParser
from timeio.parser.mqtt_devices.brightsky_dwd import BrightskyDwdApiParser
from timeio.parser.mqtt_devices.campbell_cr6 import CampbellCr6Parser
from timeio.parser.mqtt_devices.chirpstack_generic import ChirpStackGenericParser
from timeio.parser.mqtt_devices.ydoc_ml_417 import YdocMl417Parser
from timeio.parser.mqtt_devices.sine_dummy import SineDummyParser


def get_parser(parser_type, settings) -> CsvParser | JsonParser | MqttParser:
    types = {
        "csvparser": CsvParser,
        "jsonparser": JsonParser,
        "campbell_cr6": CampbellCr6Parser,
        "brightsky_dwd_api": BrightskyDwdApiParser,
        "ydoc_ml417": YdocMl417Parser,
        "chirpstack_generic": ChirpStackGenericParser,
        "sine_dummy": SineDummyParser,
    }
    klass = types.get(parser_type)
    if klass is None:
        raise NotImplementedError(f"parser {parser_type!r} not known")

    if issubclass(klass, CsvParser):
        if not settings:
            settings = {}
        default_settings = {
            "comment": "#",
            "decimal": ".",
            "na_values": None,
            "encoding": "utf-8",
            "engine": "python",
            "on_bad_lines": "warn",
            "header": None,
        }

        kwargs = settings.pop("pandas_read_csv", {})
        settings = {**default_settings, **kwargs, **settings}
        return klass(settings)

    elif issubclass(klass, JsonParser):
        if not settings:
            settings = {}
        default_settings = {
            "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        }
        kwargs = settings.pop("pandas_json_normalize", {})
        settings = {**default_settings, **kwargs, **settings}
        return klass(settings)

    return klass()
