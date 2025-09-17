from __future__ import annotations

import json
import pandas as pd
import re
import warnings

from functools import reduce

from timeio.parser.pandas_parser import PandasParser
from timeio.errors import ParsingError, ParsingWarning
from timeio.journaling import Journal

journal = Journal("JsonParser")


class JsonParser(PandasParser):
    @staticmethod
    def _clean_string(rawdata: str, comment) -> str:
        comment_re = re.escape(comment) + r".*"
        clean_string = re.sub(comment_re, "", rawdata)
        return clean_string

    @classmethod
    def _json_to_df(cls, rawdata: str, comment: str = "//") -> pd.DataFrame:
        cleaned_data = cls._clean_string(rawdata, comment)
        json_data = json.loads(cleaned_data)
        return pd.json_normalize(json_data)

    @staticmethod
    def _set_index(df: pd.DataFrame, timestamp_columns: dict) -> pd.DataFrame:
        date_columns = [d["column"] for d in timestamp_columns]
        date_format = " ".join([d["format"] for d in timestamp_columns])

        index = reduce(
            lambda x, y: x + " " + y,
            [df[c].fillna("").astype(str).str.strip() for c in date_columns],
        )

        df = df.drop(columns=date_columns)
        dt_index = pd.to_datetime(index, format=date_format, errors="coerce")
        if dt_index.isna().any():
            nat = dt_index.isna()
            warnings.warn(
                f"Could not parse {nat.sum()} of {len(df)} timestamps "
                f"with provided timestamp format {date_format!r}. First failing "
                f"timestamp: '{index[nat].iloc[0]}'",
                ParsingWarning,
            )
        index.name = None
        df.index = dt_index
        return df

    def do_parse(self, rawdata: str) -> pd.DataFrame:
        settings = self.settings.copy()
        self.logger.info(settings)

        comment = settings.get("comment")
        timestamp_columns = settings.get("timestamp_columns", {})
        df = self._json_to_df(rawdata, comment)
        try:
            df = self._set_index(df, timestamp_columns)
        except KeyError as e:
            raise ParsingError(f"Timestamp path error: {e}")
        return df
