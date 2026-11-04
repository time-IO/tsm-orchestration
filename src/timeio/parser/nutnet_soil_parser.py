from copy import deepcopy

import pandas as pd

from timeio.errors import ParsingError
from timeio.parser.csv_parser import CsvParser

VALUES_PER_SENSOR = 5
EXPECTED_FIELD_COUNT = 1 + 12 * VALUES_PER_SENSOR

DEFAULT_SETTINGS = {
    "delimiter": ",",
    "decimal": ".",
    "encoding": "utf-8",
    # Keep every row as data and use original zero-based column positions.
    "header": None,
    "names": None,
    "duplicate": False,
    "skiprows": 0,
    "skipfooter": 0,
    "comment": None,
    "na_values": [""],
    "timestamp_columns": [{"column": 0, "format": "%d.%m.%Y %H:%M:%S"}],
    # IANA Etc/GMT signs are reversed: GMT-1 is fixed UTC+01:00, without DST.
    "timezone": "Etc/GMT-1",
}


class NutNetSoilParser(CsvParser):
    """Repair NutNet soil rows and parse them with fixed CSV settings.

    Rows contain a timestamp and twelve five-value sensor groups (60 commas).
    A missing group may be written as just one empty field. On short rows,
    expand those fields from left to right by four fields, including at the
    end of a row. Blank lines are removed before CSV header/skip settings are
    applied.
    """

    def __init__(self):
        super().__init__(deepcopy(DEFAULT_SETTINGS))

    @staticmethod
    def _cleanup(rawdata: str) -> str:
        lines = []
        for line_number, line in enumerate(rawdata.splitlines(), start=1):
            line = line.rstrip()
            if not line:
                continue

            fields = line.split(",")
            missing_fields = EXPECTED_FIELD_COUNT - len(fields)
            if missing_fields <= 0:
                lines.append(line)
                continue

            # Preserve the timestamp; each empty measurement field can stand
            # for one missing sensor, including adjacent and trailing sensors.
            repaired = fields[:1]
            for field in fields[1:]:
                repaired.append(field)
                if field == "" and missing_fields >= VALUES_PER_SENSOR - 1:
                    repaired.extend([""] * (VALUES_PER_SENSOR - 1))
                    missing_fields -= VALUES_PER_SENSOR - 1

            if missing_fields:
                raise ParsingError(
                    f"NutNet soil line {line_number}: cannot repair row to "
                    f"{EXPECTED_FIELD_COUNT} fields "
                    f"(found {len(repaired)} after cleanup)"
                )
            lines.append(",".join(repaired))

        return "\n".join(lines)

    def do_parse(
        self, rawdata: str, project_name: str, thing_uuid: str
    ) -> pd.DataFrame:
        return super().do_parse(self._cleanup(rawdata), project_name, thing_uuid)
