#!/usr/bin/env python3
from __future__ import annotations

import json
import warnings
import numpy as np
import pandas as pd
import saqc
from saqc import DictOfSeries

from timeio.qc.qctools import QcTool

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")

QUALITY_COLUMNS = ["annotationType", "annotation", "measure", "userLabel", "version"]
#                  "saqc"             flag         func       label        saqc.version


class TimeIOScheme(saqc.FloatScheme):

    def toInternal(self, flags: saqc.DictOfSeries) -> saqc.Flags:
        """Translate a dict of pandas.Dataframes (each with QUALITY_COLUMNS

        )
        to a Flags object with a History (with metadata) for each frame.
        """
        data = {}
        for key, df in flags.items():  # type: str, pd.Series
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
                    "annotationType": Saqc.name,
                    "annotation": series,
                    "version": Saqc.version,
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
                out[field] = df

        return out


class Saqc(QcTool):

    name = "saqc"
    version = saqc.__version__

    def __init__(self):
        self._qc = saqc.SaQC(scheme=TimeIOScheme())

    @property
    def columns(self) -> pd.Index:
        return self._qc.columns

    def check_func_name(self, func_name: str):
        if not hasattr(saqc.SaQC, func_name):
            raise ValueError(f"Unknown qc routine {func_name} for SaQC")

    def execute(self, func_name: str, *args, **kwargs) -> Saqc:
        qc = self._qc
        func = getattr(qc, func_name)
        self._qc = func(*args, **kwargs)
        return self

    def add_data(
        self, data: dict[str, pd.Series], quality: dict[str, pd.Series] | None = None
    ):
        # First we translate from STA conform json annotations to a
        # dataframe with QUALITY_COLUMNS.
        if quality is not None:
            quality = {k: self.from_STA_annotations(q) for k, q in quality.items()}
            quality = DictOfSeries(quality)

        # Second we implicitly (TimeIOScheme.toInternal) translate from
        # the dataframe with QUALITY_COLUMNS to internal Flags and History
        # with metadata.
        new = saqc.SaQC(data, quality, scheme=TimeIOScheme())
        self._qc[new.columns] = new

    def get_quality(self) -> dict[str, pd.Series]:
        # First we do an implicit back translation (TimeIOScheme.toExternal), then we
        # translate the resulting dataframe with QUALITY_COLUMNS back to STA compatible
        # json annotations.
        return {k: self.to_STA_annotations(df) for k, df in self._qc.flags.items()}

    def get_data(self) -> dict[str, pd.Series]:
        return self._qc.data  # type: ignore

    def from_STA_annotations(self, s: pd.Series) -> pd.DataFrame:
        """Make a pandas.Dataframe with QUALITY_COLUMNS from a pandas.Series with
        timeIO/STA standard quality labels (structured JSON).
        """
        df = pd.json_normalize(s)
        df.index = s.index
        if df.empty:
            df = df.reindex(columns=QUALITY_COLUMNS)
        df.columns = df.columns.str.removeprefix("properties.")
        return df[QUALITY_COLUMNS]

    def to_STA_annotations(self, frame: pd.DataFrame) -> pd.Series:
        """Make a pandas.Series with standard timeIO/STA json quality labels
        from a flag dataframe (from a saqc result).
        """

        # Basically we just add a level of nesting here.
        def jsonify(row: pd.Series):
            return json.dumps(
                {
                    "annotationType": row["annotationType"],
                    "annotation": row["annotation"],
                    "properties": {
                        "version": row["version"],
                        "measure": row["measure"],
                        "userLabel": row["userLabel"],
                    },
                }
            )

        return frame.apply(jsonify, axis=1)
