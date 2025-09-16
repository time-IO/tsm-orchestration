from __future__ import annotations

import re
import warnings
import yaml
import os
import pytz

from functools import reduce
from io import StringIO
from typing import TypeVar

import pandas as pd
import numpy as np

from timeio.parser.pandas.parser import PandasParser
from timeio.parser.pandas.csv.utils import get_header, pandafy_headerline
from timeio.errors import ParsingError, ParsingWarning
from timeio.journaling import Journal

parsedT = TypeVar("parsedT")
journal = Journal("CsvParser")


class CsvParser(PandasParser):
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

    def do_parse(self, rawdata: str, project_name: str, thing_uuid: str):
        """
        Parse rawdata string to pandas.DataFrame
        rawdata: the unparsed content
        NOTE:
            we need to preserve the original column numbering
        """
        settings = self.settings.copy()
        self.logger.info(settings)

        timestamp_columns = settings.pop("timestamp_columns")
        ts_indices = [i["column"] for i in timestamp_columns]
        header_line = settings.get("header", None)
        custom_names = settings.pop("names", None)
        delimiter = settings.get("delimiter", ",")
        duplicate = settings.pop("duplicate", False)
        tz_info = settings.pop("timezone", None)
        if header_line is not None:
            header_raw = get_header(rawdata, header_line)
            self.logger.debug(f"HEADER: {header_raw}")
        if tz_info is not None:
            if tz_info not in pytz.all_timezones:
                raise ValueError(f"Invalid timezone string: {tz_info}")

        if comment_regex := settings.pop("comment", r"(?!.*)"):
            if isinstance(comment_regex, str):
                comment_regex = (comment_regex,)
            comment_regex = "|".join(comment_regex)

        rows = []
        for i, row in enumerate(rawdata.splitlines()):
            if i == header_line:
                # we might have comments at the header line as well
                header_raw_clean = re.sub(comment_regex, "", row).strip()
                header_names = pandafy_headerline(header_raw_clean, delimiter)
                settings["names"] = header_names
                settings["header"] = None
                continue
            rows.append(row)
        rawdata = "\n".join(rows)

        try:
            df = pd.read_csv(StringIO(rawdata), **settings)
        except (pd.errors.EmptyDataError, IndexError):  # both indicate no data
            df = pd.DataFrame()

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

        df = self._set_index(df, timestamp_columns)
        if tz_info is not None:
            try:
                df.index = df.index.tz_localize(tz_info)
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
        return df
