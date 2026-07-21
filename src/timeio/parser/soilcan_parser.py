import re
import subprocess
import tempfile

from pathlib import Path
from typing import Any, TypedDict, Literal

import pandas as pd

from timeio.errors import ParsingError
from timeio.parser.pandas_parser import PandasParser
from timeio.parser.csv_parser import CsvParser

EXE = Path(__file__).parent / "bin" / "dump_dbd"

DEFAULT_SETTINGS = {
    "delimiter": ",",
    "timestamp_columns": [{"column": 0, "timestamp_format": "%Y/%m/%d %H:%M:%S.%f"}],
    # TODO: Check if this is True
    "timezone": "UTC",
}

TABLE_MAP = {
    "operating-parameters": 0,
    "sensor-data": 1,
    "weighing-data": 2,
}


class SoilcanParserSetting(TypedDict):
    type: Literal["operating-parameters", "sensor-data", "weighing-data"]
    header: bool


class SoilcanParser(PandasParser):
    is_binary = True

    def __init__(self, settings: SoilcanParserSetting):
        settings = settings.copy()

        self.table_no = TABLE_MAP[settings.pop("type")]
        include_header = settings.pop("header")

        csv_settings = (
            DEFAULT_SETTINGS
            | settings
            | {
                "header": 0 if include_header else None,
                "skiprows": 0 if include_header else 1,
            }
        )

        super().__init__(csv_settings)

    def _dump_data(self, rawdata: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".DBD") as tmp:
            tmp.write(rawdata)
            tmp.flush()

            try:
                result = subprocess.run(
                    [str(EXE), "-n", "-d", tmp.name],
                    capture_output=True,
                    check=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            except (OSError, subprocess.CalledProcessError) as e:
                detail = getattr(e, "stderr", None)
                message = f"{self.__class__.__name__}: failed to decode DBD file"
                if detail:
                    message = f"{message}: {detail.strip()}"
                raise ParsingError(message) from e

        return result.stdout

    def do_parse(
        self, rawdata: Any, project_name: str, thing_uuid: str
    ) -> pd.DataFrame:

        dumped_data = self._dump_data(rawdata)
        blocks = [
            b for b in re.split(r"(?m)(?=^[^\d])", dumped_data.strip()) if b.strip()
        ]

        parser = CsvParser(self.settings)
        df = parser.do_parse(
            blocks[self.table_no], project_name=project_name, thing_uuid=thing_uuid
        )
        self._start_date = parser._start_date
        self._end_date = parser._end_date

        return df
