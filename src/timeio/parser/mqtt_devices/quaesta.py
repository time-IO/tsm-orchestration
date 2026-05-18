from __future__ import annotations

from typing import Any
from datetime import datetime

from timeio.parser.mqtt_parser import MqttParser, Observation

"""
example payload for rawdata
{"RecordNum":1,"DateTimeUTC":"2026/03/25 13:20:52","P1_mb":984.58,"P2_mb":983.65,"T1_degC":15.6,"RH1":40.2,"Vbat":14.05,"P3_mb":983.90,"N1Cts":54,"N1ET_sec":44,"N1T(C)":11.3,"N1RH":0.2}
RecordNum should not be stored, DateTimeUTC should be transformed into datetime.datetime
"""


class QuaestaParser(MqttParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        #
        rawdata.pop("RecordNum")
        timestamp = datetime.strptime(rawdata.pop("DateTimeUTC"), "%Y/%m/%d %H:%M:%S")
        out = []
        for key, value in rawdata.items():
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
                # value is NaN or None
                continue
        return out
