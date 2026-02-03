#!/usr/bin/env python3

import warnings

import numpy as np
import pandas as pd

import saqc

from timeio.qc.qcfunction import QcFunction

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")

QUALITY_COLUMNS = ["annotationType", "annotation", "measure", "userLabel", "version"]
#                  "saqc"             flag         func       label        saqc.version


class STAMPLATEScheme(saqc.FloatScheme):

    @staticmethod
    def toSTAannotations(row: pd.Series) -> dict[str, str | dict[str, str]]:
        """Create a dict that can be translated to a structured json according to
        the STAMPLATE specs."""
        return {
            "annotationType": row["annotationType"],
            "annotation": str(row["annotation"]),
            "properties": {
                "measure": row["measure"],
                "userLabel": row["userLabel"],
                "version": row["version"],
            },
        }

    @staticmethod
    def fromSTAannotations(s: pd.Series) -> pd.DataFrame:
        """Make a pandas.Dataframe with QUALITY_COLUMNS from a pandas.Series with
        timeIO/STA standard quality labels (dicts parsed from a structured JSON).
        """
        df = pd.json_normalize(list(s))
        df.index = s.index
        if df.empty:
            df = df.reindex(columns=QUALITY_COLUMNS)
        df.columns = df.columns.str.removeprefix("properties.")
        return df[QUALITY_COLUMNS]

    def toInternal(self, flags: saqc.DictOfSeries) -> saqc.Flags:
        """Translate a dict of pandas.Series of json quality annotations
        to a Flags object with a History (with metadata) for each series.
        """

        data = {}
        for key, series in flags.items():  # type: str, pd.Series
            df: pd.DataFrame = self.fromSTAannotations(series)
            history = saqc.core.History(index=df.index)
            for (anno, measure, user_label), values in df.groupby(
                ["annotation", "measure", "userLabel"]
            ):
                column = pd.Series(np.nan, index=df.index)
                column.loc[values.index] = self(anno)
                kwargs = {"label": user_label}
                history.append(column, meta={"func": measure, "kwargs": kwargs})
            data[key] = history
        return saqc.Flags(data)

    def toExternal(
        self, flags: saqc.Flags, attrs: dict | None = None
    ) -> saqc.DictOfSeries:
        """
        Translate from internal Flags object with multiple Histories (with metadata)
        to a dict of pandas.Dataframes, each with QUALITY_COLUMNS.
        """
        UNFLAGGED = saqc.UNFLAGGED  # noqa
        out = saqc.DictOfSeries()

        tflags = super().toExternal(flags, attrs=attrs)
        for field in tflags.columns:
            series: pd.Series = tflags[field]
            # The df has the index from series.
            df = pd.DataFrame(
                {
                    "annotationType": "SaQC",
                    "annotation": series,
                    "version": saqc.__version__,
                    "measure": "",  # filled below
                    "userLabel": "",  # filled below
                }
            )

            assert set(df.columns) == set(QUALITY_COLUMNS)

            history = flags.history[field]
            for col in history.columns:
                # We map the meta entries (func and label) to the respective rows
                valid = (history.hist[col] != UNFLAGGED) & history.hist[col].notna()
                meta = history.meta[col]
                df.loc[valid, "measure"] = meta["func"]
                df.loc[valid, "userLabel"] = meta["kwargs"].get("label", None)
                series = pd.Series(index=df.index, dtype=object)
                if not df.empty:
                    series = df.apply(self.toSTAannotations, axis=1)
                out[field] = series

        return out


def init_saqc(data: dict[str, pd.DataFrame]) -> saqc.SaQC:
    values = {}
    flags = {}

    for k, df in data.items():
        values[k] = df["data"]
        flags[k] = df.get("quality", pd.Series(None, index=df["data"].index))

    return saqc.SaQC(
        data=saqc.DictOfSeries(values),
        flags=saqc.DictOfSeries(flags),
        scheme=STAMPLATEScheme(),
    )


import ast
from saqc.parsing.visitor import ConfigFunctionParser


def parse_generic_function(func: QcFunction):

    # NOTE:
    # The generic function parser is not as well exposed in
    # SaQC as is could be, that's why we need to go the extra
    # mile and built a valid saqc config-file function
    func_string = (
        f"{func.func_name}({','.join('='.join(item) for item in func.params.items())})"
    )
    tree = ast.parse(func_string, mode="eval").body
    _, kwargs = ConfigFunctionParser().parse(tree)
    return kwargs["func"]


def execute_qc_function(qc: saqc.SaQC, func: QcFunction) -> saqc.SaQC:
    saqc_func = getattr(qc, func.func_name)
    if func.func_name == "flagRange":
        # NOTE: needed to work around a SaQC-Bug,
        #       that will be fixed in the next release
        # TODO: remove entire block after the bug is fixed
        for f in func.field_names:
            saqc_func = getattr(qc, func.func_name)
            qc = saqc_func(field=f, target=func.target_names, **func.params)
        return qc
    if func.func_name.endswith("Generic"):
        # NOTE: we need to parse the user given processing input in a save manner
        func.params["func"] = parse_generic_function(func)
    return saqc_func(field=func.field_names, target=func.target_names, **func.params)
