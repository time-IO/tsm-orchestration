from __future__ import annotations

import re
import warnings
import yaml
import os
import pytz
from typing import TypeVar, Any
import pandas as pd
import numpy as np
from io import StringIO
from functools import reduce

from timeio.parser.pandas_parser import PandasParser
from timeio.errors import ParsingError, ParsingWarning, EmptyDataError
from timeio.journaling import Journal

parsedT = TypeVar("parsedT")
journal = Journal("CsvParser", errors="warn")

DEFAULT_SETTINGS = {
    "comment": "#",
    "decimal": ".",
    "na_values": None,
    "encoding": "utf-8",
    "engine": "python",
    "on_bad_lines": "warn",
    "header": None,
}


class CsvParser(PandasParser):
    def __init__(self, settings: dict[str, Any] | None = None):
        settings = dict(settings or {})
        pandas_read_csv = settings.pop("pandas_read_csv", None) or {}
        super().__init__({**DEFAULT_SETTINGS, **settings, **pandas_read_csv})

    @staticmethod
    def _set_index(df: pd.DataFrame, timestamp_columns: dict) -> pd.DataFrame:
        date_columns = [df.columns[d["column"]] for d in timestamp_columns]
        try:
            date_format = " ".join([d["format"] for d in timestamp_columns])
        except:
            date_format = " ".join([d["timestamp_format"] for d in timestamp_columns])

        # for c in date_columns:
        #     if c not in df.columns:
        #         raise ParsingError(f"Timestamp column {c} does not exist. ")

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

    def _write_mapping_yaml(
        self,
        df_default: pd.DataFrame,
        header_names: list,
        ts_indices: list,
        project_name: str,
        thing_uuid: str,
    ):
        column_mapping = dict(zip(df_default.columns, header_names))
        column_mapping = {
            thing_uuid: {k: v for k, v in column_mapping.items() if k not in ts_indices}
        }
        output_dir = f"/tmp/datastream_mapping/{project_name}/mappings"
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(f"{output_dir}/{thing_uuid}.yaml", "w") as f:
                yaml.dump(column_mapping, f, sort_keys=False)
            self.logger.info(
                f"Successfully created mapping yaml for thing {thing_uuid}"
            )
        except Exception as e:
            warnings.warn(
                f"Failed to create mapping yaml for thing {thing_uuid}: {e}",
                ParsingWarning,
            )

    @staticmethod
    def _validate_settings(settings):
        tz_info = settings.get("timezone", None)

        if tz_info is not None and tz_info not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone string: {tz_info}")

        return settings

    @staticmethod
    def _define_comment_regex(settings: dict[str, Any]) -> str:
        comments = settings.pop("comment", "")
        if not comments:
            return ""
        if isinstance(comments, str):
            comments = [comments]
        comments = [re.escape(c) for c in comments]
        return "|".join(comments)

    @staticmethod
    def _apply_skipping(lines, skiprows, skipfooter):
        if skiprows is None:
            skiprows = []
        # in Config-DB or pandas_read_csv JSON, skiprows is stored as an integer
        if isinstance(skiprows, int):
            skiprows = range(skiprows)
        # in DSM-DB skiprows is stored as a string of comma-separated integers
        if isinstance(skiprows, str):
            skiprows = [int(i) for i in skiprows.split(",")]
            if len(skiprows) == 1:
                skiprows = range(skiprows[0])
        skiprows = set(skiprows)

        if skipfooter is None:
            skipfooter = 0

        lines = [line for i, line in enumerate(lines) if i not in skiprows]
        return lines[: -skipfooter or None]

    @staticmethod
    def _handle_header(lines, settings, header_line, comment_regex):

        if header_line is None:
            return lines, None

        raw_header = lines[header_line]
        header_raw_clean = re.sub(comment_regex, "", raw_header).strip()
        delimiter = settings.get("delimiter", ",")
        header_names = pandafy_headerline(header_raw_clean, delimiter)

        settings["names"] = header_names
        settings["header"] = None
        lines = lines[header_line + 1 :]

        return lines, header_names

    @staticmethod
    def _filter_comments(lines: list[str], comment_regex: str) -> list[str]:
        """Remove everything after a comment marker in each line"""
        if not comment_regex:
            return lines
        regex = rf"({comment_regex}).*"
        return [re.sub(regex, "", line.strip()) for line in lines]

    def do_parse(
        self, rawdata: str, project_name: str, thing_uuid: str
    ) -> pd.DataFrame:
        """
        Parse rawdata string to pandas.DataFrame
        rawdata: the unparsed content
        NOTE:
            we need to preserve the original column numbering
        """
        if len(rawdata) == 0:
            raise EmptyDataError("No data given")

        settings = self._validate_settings(self.settings.copy())
        self.logger.info(settings)

        timestamp_columns = settings.pop("timestamp_columns")
        ts_indices = [i["column"] for i in timestamp_columns]
        header_line = settings.get("header", None)

        # handle deprecated settings keywords for skipping rows and footers
        skiprows = settings.pop("skiprows", None)
        headlines_to_exclude = settings.pop("headlines_to_exclude", None)
        skiprows = skiprows if skiprows is not None else headlines_to_exclude or 0
        skipfooter = settings.pop("skipfooter", None)
        footlines_to_exclude = settings.pop("footlines_to_exclude", None)
        skipfooter = skipfooter if skipfooter is not None else footlines_to_exclude or 0

        custom_names = settings.pop("names", None)
        duplicate = settings.pop("duplicate", False)
        tz_info = settings.pop("timezone", None)

        comment_regex = self._define_comment_regex(settings)

        lines = rawdata.splitlines()
        lines = self._apply_skipping(lines, skiprows, skipfooter)
        lines, header_names = self._handle_header(
            lines, settings, header_line, comment_regex
        )
        lines = self._filter_comments(lines, comment_regex)

        rawdata = "\n".join(lines)

        try:
            df = pd.read_csv(StringIO(rawdata), **settings)
        except (pd.errors.EmptyDataError, IndexError):  # both indicate no data
            df = pd.DataFrame()
        except Exception as e:
            raise ParsingError("Parsing failed") from e

        if df.empty:
            return pd.DataFrame(index=pd.DatetimeIndex([]))

        if header_line is not None:
            if duplicate:
                df_default_names = df.copy()
                df_default_names.columns = range(len(df.columns))
                df.columns = header_names
                if np.array_equal(df.to_numpy(), df_default_names.to_numpy()):
                    self._write_mapping_yaml(
                        df_default_names,
                        header_names,
                        ts_indices,
                        project_name,
                        thing_uuid,
                    )
                    df_default_names = df_default_names.drop(
                        columns=ts_indices, errors="ignore"
                    )
                    df = pd.concat([df, df_default_names], axis=1)
                else:
                    df = df_default_names
                    warnings.warn(
                        "Comparison of header based data and position based "
                        "data failed. Positions will be used instead.",
                        ParsingWarning,
                    )

        # If no header is given, we always use column positions or custom names if given
        else:
            if custom_names:
                if len(custom_names) != len(df.columns):
                    raise ParsingError(
                        "Number of custom column names does not match number of columns in CSV."
                    )
                else:
                    df.columns = custom_names
            else:
                df.columns = range(len(df.columns))
        df, timestamp_columns = self.normalize_unix_timestamps(
            df,
            timestamp_columns,
            "csv",
        )
        df = self._set_index(df, timestamp_columns)
        if tz_info is not None:
            try:
                if df.index.tz is None:
                    df.index = df.index.tz_localize(tz_info)
                else:
                    journal.info(
                        f"Timestamps are already timezone aware, converting '{df.index.tz}' -> '{tz_info}'",
                        thing_uuid,
                    )
                    df.index = df.index.tz_convert(tz_info)
            except TypeError:
                raise ParsingError(
                    f"Cannot localize timezone '{tz_info}': index is already timezone aware with tz ({df.index.tz})."
                )

        # remove rows with broken dates
        df = df.loc[df.index.notna()]

        if df.shape[0] == 0:
            warnings.warn(
                "Parsing resulted in empty dataset.",
                ParsingWarning,
            )

        self.logger.debug(f"data.shape={df.shape}")

        self._start_date = df.index.min()
        self._end_date = df.index.max()
        return df


def filter_lines(rawdata: str, comment_regex: str) -> str:
    lines = []
    for line in rawdata.splitlines():
        if not re.match(comment_regex, line):
            lines.append(line)
    return "\n".join(lines)


def get_header(rawdata: str, header_line: int) -> str:
    for i, line in enumerate(rawdata.splitlines()):
        if i == header_line:
            return line
    raise ValueError(f"header line {header_line} not found")


def pandafy_headerline(header_raw: str, delimiter: str) -> list[str]:
    mock_cvs = StringIO(header_raw + "\n\n")
    df = pd.read_csv(mock_cvs, delimiter=delimiter)
    return df.columns.to_list()
