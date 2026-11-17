from __future__ import annotations

from typing import Any
from datetime import datetime

from timeio.errors import ParsingError
from timeio.parser.mqtt_parser import MqttParser, Observation


class YdocMl417Parser(MqttParser):
    HEADERS = ("MINVi", "AVGVi", "AVGCi", "P1*", "P2", "P3", "P4")

    # mqtt_ingest/test-logger-pb/test/data/jsn
    # {
    # "device":
    #   {"sn":99073020,"name":"UFZ","v":"4.2B5","imei":353081090730204,"sim":89490200001536167920},
    # "channels":[
    #   {"code":"SB","name":"Signal","unit":"bars"},
    #   {"code":"MINVi","name":"Min voltage","unit":"V"},
    #   {"code":"AVGVi","name":"Average voltage","unit":"V"},
    #   {"code":"AVGCi","name":"Average current","unit":"mA"},
    #   {"code":"P1*","name":"pr2_1_10","unit":"m3/m3"},
    #   {"code":"P2","name":"pr2_1_20","unit":"m3/m3"},
    #   {"code":"P3","name":"pr2_1_30","unit":"m3/m3"},
    #   {"code":"P4","name":"pr2_1_40","unit":"m3/m3"},
    #   {}],
    # "data":[
    #   {"$ts":230116110002,"$msg":"WDT;pr2_1"},    <== we ignore that (*)
    #   {"$ts":230116110002,"MINVi":3.74,"AVGVi":3.94,"AVGCi":116,"P1*":"0*T","P2":"0*T","P3":"0*T","P4":"0*T"},
    #   {}]}

    def do_parse(self, rawdata: Any, origin: str = "", **kwargs) -> list[Observation]:
        if "data/jsn" not in origin:
            return self.ignore("only topics with 'data/jsn' contain data")

        # data = payload['data'][1]
        try:
            rows = rawdata["data"]
        except (KeyError, TypeError) as e:
            raise ParsingError("Message must contain the field 'data'") from e
        if not isinstance(rows, list):
            raise ParsingError("Field 'data' must be a list")

        ret = []
        for data in rows:
            try:
                raw_ts = data["$ts"]
                values = [data[h] for h in self.HEADERS]
            except (KeyError, TypeError):
                # rows without all keys, see the example above (*)
                self.skip("incomplete rows")
                continue
            try:
                ts = datetime.strptime(str(raw_ts), "%y%m%d%H%M%S")
            except ValueError as e:
                raise ParsingError(
                    f"Invalid '$ts' {raw_ts!r}, expected format 'YYMMDDhhmmss'"
                ) from e
            for pos, (header, value) in enumerate(zip(self.HEADERS, values)):
                try:
                    ret.append(Observation(ts, value, origin, pos, header=header))
                except ValueError:
                    self.skip("empty values")
        return ret
