from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from timeio.parser.mqtt_parser import MqttParser, Observation

"""
example payload for rawdata
 {
  "stationID": "Site118",
  "loggerID": "QI-DL2200-SN-25100118",
  "type": "dataCRNS",
  "timestampISO8601": "2026-05-20T16:00:00Z",
  "timestampEpoch": 1779292800,
  "dataSelect": "p3t3h3n1e1s1w1w2",
  "recordNum": 4,
  "P1_mb": 929.2,
  "P2_mb": 928.11,
  "T1_degC": 26.6,
  "RH1_pct": 16.8,
  "Vbat_V": 12.18,
  "P3Extern_mb": 928.2,
  "T3Extern_degC": 26.2,
  "RH3Extern_pct": 18.6,
  "N1_Cts": 2995,
  "N1ET_sec": 3600,
  "N1T_degC": 32.9,
  "N1RH_pct": 16.4,
  "SMT100_1_1": 12428,
  "SMT100_1_2": 8.86,
  "SMT100_1_3": 16.56,
  "SMT100_1_4": 25.97,
  "SMT100_1_5": 11.62,
  "SMT100_2_1": 12118,
  "SMT100_2_2": 9.77,
  "SMT100_2_3": 18.38,
  "SMT100_2_4": 25.86,
  "SMT100_2_5": 11.59
}
RecordNum should not be stored, DateTimeUTC should be transformed into datetime.datetime
"""


class QuaestaParser(MqttParser):
    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        timestamp = datetime.strptime(
            rawdata.pop("timestampISO8601"), "%Y-%m-%dT%H:%M:%SZ"
        )
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        out = []
        if rawdata.get("type") != "dataCRNS":
            return out
        for key, value in rawdata.items():
            if key in (
                "stationID",
                "loggerID",
                "type",
                "timestampEpoch",
                "dataSelect",
                "recordNum",
            ):
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
                # value is NaN or None
                continue
        return out
