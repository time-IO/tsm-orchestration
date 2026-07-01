import re
import subprocess
import tempfile

from pathlib import Path
from typing import Any

import pandas as pd

from timeio.errors import ParsingError
from timeio.parser.pandas_parser import PandasParser
from timeio.parser.csv_parser import CsvParser

EXE = Path(__file__).parent / "bin" / "dump_dbd"
SETTINGS = {
    "delimiter": ",",
    "timestamp_columns": [{"column": 0, "format": "%Y/%m/%d %H:%M:%S.%f"}],
    # TODO: Check if this is True
    "timezone": "UTC",
    "header": 0,
}


class SoilcanParser(PandasParser):
    is_binary = True

    def __init__(self):
        super().__init__(SETTINGS)

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
    ) -> list[pd.DataFrame]:

        dumped_data = self._dump_data(rawdata)
        blocks = [
            b for b in re.split(r"(?m)(?=^[^\d])", dumped_data.strip()) if b.strip()
        ]

        parser = CsvParser(self.settings)
        out: list[pd.DataFrame] = []
        self._start_date = None
        self._end_date = None

        for b in blocks:
            frames = parser.do_parse(
                b, project_name=project_name, thing_uuid=thing_uuid
            )
            for df in frames:
                if df.empty:
                    continue

                frame_start = df.index.min()
                frame_end = df.index.max()

                if self._start_date is None or frame_start < self._start_date:
                    self._start_date = frame_start
                if self._end_date is None or frame_end > self._end_date:
                    self._end_date = frame_end

                out.append(df)

        return out
