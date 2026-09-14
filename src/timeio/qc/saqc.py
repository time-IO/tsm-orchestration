#!/usr/bin/env python3

import logging
import json

import numpy as np
import pandas as pd

import saqc
from saqc.funcs.generic import compileGeneric

from timeio.qc.qcfunction import QcFunction, QcFunctionStream

logger = logging.getLogger("run-quality-control")

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    logger.warning("could not import module 'tsm_user_code'")

QUALITY_COLUMNS = ["annotationType", "annotation", "measure", "userLabel", "version"]
#                  "saqc"             flag         func       label        saqc.version
FINAL_QUALITY_COLUMNS = ["value", "metric", "parameters", "dimension"]

# used to identify which function calls are allowed to overwrite a `target`,
# TODO: use the new SaQC function mode variable to infer programmatically
PROCESSING_FUNCTIONS = {"processGeneric", "rolling"}

saqc.options.field_target = "append"


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
    def _fromSTAannotations(s: pd.Series) -> pd.DataFrame:
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
            df: pd.DataFrame = self._fromSTAannotations(series)
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
                df.loc[valid, "userLabel"] = meta["kwargs"].get("label") or ""
                series = pd.Series(index=df.index, dtype=object)
                if not df.empty:
                    series = df.apply(self.toSTAannotations, axis=1)
                out[field] = series

        return out


class STAMPLATESchemeFinal(saqc.FloatScheme):
    SAQC_DOCS_URL = "https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html"
    SAQC_DIMENSION_URL = (
        "https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/blob/main/"
        "src/timeio/qc/saqc.py"
    )
    INTERNAL_KWARGS = {"field", "target", "dfilter", "flag", "label"}
    # SaQC represents unflagged values as -inf, which is not valid JSON as a number.
    UNFLAGGED_LABEL = "-inf"

    @staticmethod
    def _metric_name(metric: str) -> str:
        return str(metric).rstrip("/").rsplit("/", maxsplit=1)[-1]

    @classmethod
    def _parameters(cls, kwargs: dict) -> dict:
        return {
            key: value.item() if hasattr(value, "item") else value
            for key, value in kwargs.items()
            if key not in cls.INTERNAL_KWARGS
        }

    @staticmethod
    def _quality_measurement_to_row(measurement: dict) -> dict:
        return {
            "value": measurement["value"],
            "metric": STAMPLATESchemeFinal._metric_name(measurement["metric"]),
            "parameters": measurement["parameters"],
            "dimension": measurement["dimension"],
        }

    @staticmethod
    def _from_sta_annotations(s: pd.Series) -> pd.DataFrame:
        """
        Make a pandas.Dataframe with QUALITY_COLUMNS from a pandas.Series with
        timeIO/STA standard quality labels (dicts parsed from a structured JSON).
        """
        rows = []
        index = []
        for idx, obj in s.items():
            for measurement in obj["resultQuality"]["hasQualityMeasurements"]:
                rows.append(
                    STAMPLATESchemeFinal._quality_measurement_to_row(measurement)
                )
                index.append(idx)

        df = pd.DataFrame(rows, index=index)
        if df.empty:
            df = df.reindex(columns=FINAL_QUALITY_COLUMNS)
        return df[FINAL_QUALITY_COLUMNS]

    def toInternal(self, flags: saqc.DictOfSeries) -> saqc.Flags:
        """
        Translate a dict of pandas.Series of json quality annotations
        to a Flags object with a History (with metadata) for each series.
        """

        data = {}
        for key, series in flags.items():  # type: str, pd.Series
            df: pd.DataFrame = self._from_sta_annotations(series)
            history = saqc.core.History(index=series.index)
            if not df.empty:
                df["_parameters_key"] = df["parameters"].map(
                    lambda params: json.dumps(params, sort_keys=True)
                )
                for (value, metric, _), values in df.groupby(
                    ["value", "metric", "_parameters_key"]
                ):
                    column = pd.Series(np.nan, index=series.index)
                    column.loc[values.index] = self(value)
                    parameters = values["parameters"].iloc[0]
                    history.append(
                        column, meta={"func": metric, "kwargs": parameters}
                    )
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

        for field in flags.columns:
            history = flags.history[field]
            index = history.index
            size = len(index)
            result = np.full(size, None, dtype=object)
            measurements = [[] for _ in range(size)]
            dimension = self.SAQC_DIMENSION_URL
            unflagged = self.UNFLAGGED_LABEL
            for col in history.columns:
                # We map the meta entries (func and label) to the respective rows
                column = history.hist[col]
                history_meta = history.meta[col]
                parameters = self._parameters(history_meta.get("kwargs") or {})
                metric = f"{self.SAQC_DOCS_URL}#saqc.SaQC.{history_meta['func']}"
                values = column.to_numpy()
                flagged = (column != UNFLAGGED).to_numpy() & column.notna().to_numpy()
                measurement_idx = col + 1
                template = {
                    "jsonld.id": f"qualityMeasurement_{measurement_idx}",
                    "value": unflagged,
                    "metric": metric,
                    "parameters": parameters,
                    "dimension": dimension,
                }
                for pos in range(size):
                    if flagged[pos]:
                        measurement = template.copy()
                        measurement["value"] = values[pos].item()
                    else:
                        measurement = template.copy()
                    measurements[pos].append(measurement)

            for pos, inline_measurements in enumerate(measurements):
                result[pos] = {
                    "resultQuality": {
                        "hasQualityMeasurements": inline_measurements,
                        "primaryQualityMeasurement": inline_measurements[-1],
                    }
                }
            out[field] = pd.Series(result, index=index, dtype=object)

        return out


class SaQCWrapper:
    def __init__(self, data: dict[QcFunctionStream, pd.DataFrame]):
        values = {}
        flags = {}

        for k, df in data.items():
            values[k.alias] = df["data"]
            flags[k.alias] = df.get("quality", pd.Series(None, index=df["data"].index))

        self._qc = saqc.SaQC(
            data=saqc.DictOfSeries(values),
            flags=saqc.DictOfSeries(flags),
            scheme=STAMPLATEScheme(),
        )
        # we keep the original data to check for modifications later
        self._input_data = data
        self._streams = {s.alias: s for s in data.keys()}

    @property
    def data(self) -> dict[QcFunctionStream, pd.DataFrame]:
        out = {}
        for col in self._qc.columns:
            out[self._streams[col]] = pd.DataFrame(
                {"data": self._qc.data[col], "quality": self._qc.flags.get(col, None)}
            )
        return out

    def execute(self, func: QcFunction):
        # NOTE:
        # This is a (temporary) safeguard as SaQC is currently failing hard when
        # appending to an empty Datastream. If this issue is solved in SaQC we
        # should remove this block.
        # https://git.ufz.de/rdm-software/saqc/-/work_items/546
        empty_targets = [
            t
            for t in func.target_names
            if t in self._qc.columns and self._qc.data[t].empty
        ]
        if empty_targets:
            logger.warning(
                f"skipping '{func.func_name}' as it is targeting the empty datastream(s) {empty_targets}"
            )
            return

        # add targets
        for stream in func.targets:
            self._streams[stream.alias] = stream

        saqc_func = getattr(self._qc, func.func_name)

        if func.func_name.endswith("Generic"):
            func.params["func"] = compileGeneric(func.params.pop("function"))

        self._qc = saqc_func(
            field=func.field_names, target=func.target_names, **func.params
        )

    def data_is_modified(self, stream: QcFunctionStream) -> bool:
        if stream in self._input_data:
            called_qc_funcs = [e["func"] for e in self._qc._history[stream.alias].meta]
            for func_name in called_qc_funcs:
                if func_name in PROCESSING_FUNCTIONS:
                    return True
        return False

    def index_is_modified(self, stream: QcFunctionStream) -> bool:
        return not self._qc._data[stream.alias].index.equals(
            self._input_data[stream]["data"].index
        )
