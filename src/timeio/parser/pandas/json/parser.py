from __future__ import annotations

import json
import pandas as pd
import re

from timeio.parser.pandas.parser import PandasParser
from timeio.errors import ParsingError


class JsonParser(PandasParser):
    def _clean(self, rawdata: str, comment) -> str:
        comment_re = re.escape(comment) + r".*"
        cleaned_data = re.sub(comment_re, "", rawdata)
        return cleaned_data

    def _json_to_df(self, rawdata: str, comment: str = "//") -> pd.DataFrame:
        cleaned_data = self._clean(rawdata, comment)
        json_data = json.loads(cleaned_data)
        return pd.json_normalize(json_data)

    def do_parse(self, rawdata: str) -> pd.DataFrame:
        settings = self.settings.copy()
        self.logger.info(settings)

        comment = settings.get("comment")
        timestamp_paths = settings.get("timestamps")

        df = self._json_to_df(rawdata, comment)
        try:
            df = self._set_index(df, timestamp_paths)
        except KeyError as e:
            raise ParsingError(f"Timestamp path error: {e}")
        return df
