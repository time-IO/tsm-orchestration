#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime
import json
import logging
import subprocess
import sys
import typing
import warnings
from typing import Any, Hashable, Literal, cast

import pandas as pd
import requests
import saqc
from psycopg import Connection, sql
from psycopg.rows import dict_row
from saqc import DictOfSeries, Flags

try:
    from psycopg_pool import ConnectionPool
except ImportError:
    ConnectionPool = typing.TypeVar("ConnectionPool")  # noqa


from timeio.common import ObservationResultType
from timeio.errors import DataNotFoundError, UserInputError, NoDataWarning
from timeio.typehints import DbRowT, JsonObjectT
from timeio.journaling import Journal
from timeio import feta

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
TimestampT = typing.Union[datetime.datetime.timestamp, pd.Timestamp]


class SaQCFuncT(typing.Protocol):
    def __call__(self, qc: saqc.SaQC, *args: Any, **kwargs: Any) -> saqc.SaQC: ...


journal = Journal("QualityControl")

_OBS_COLUMNS = [
    "result_time",
    "result_type",
    "result_number",
    "result_string",
    "result_json",
    "result_boolean",
    "result_quality",
]


def update_timeio_user_code():
    """
    Function to install/upgrade the python package [1], that
    provide the custom saqc user code during runtime.

    References
    ----------
    [1]: https://codebase.helmholtz.cloud/ufz-tsm/tsm-dataprocessing-extension
    """

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "git+https://codebase.helmholtz.cloud/ufz-tsm/tsm-dataprocessing-extension.git",
        ]
    )


def dict_update_to_list(dict_: dict, key: Hashable, value: Any) -> None:
    """
    Updates dict values inplace. Present keys are updated by casting
    the current value to a list, which then contains the current and
    the new value.

    d = {"a": 0}
    dict_update_to_list(d, "a", 99)
    d ==> {"a": [0, 99]}
    dict_update_to_list(d, "a", 99)
    d ==> {"a": [0, 99, 99]}
    """
    if (curr := dict_.get(key)) is None:
        dict_[key] = value
    elif isinstance(curr, list):
        dict_[key].append(value)
    else:
        dict_[key] = [dict_[key], value]


def ping_dbapi(base_url):
    r = requests.get(f"{base_url}/health")
    r.raise_for_status()


def timestamp_from_string(ts: str) -> pd.Timestamp | None:
    if ts is None:
        return None
    return pd.Timestamp(ts)


class KwargsScheme(saqc.core.core.FloatScheme):

    @staticmethod
    def get_meta_per_row(history: saqc.core.history.History) -> pd.DataFrame:
        """
        Returns a dataframe with the following columns:
         - func: str - name of last applied function (might be an empty str)
         - kwargs: dict - kwargs of last applied function (might be an empty dict)
        """

        # meta: (list of dicts with keys: func, args, kwargs)
        #   [{...}, {...}, {...}]
        # history            -> idx   ->   meta lookup
        #    0    1    2
        #   nan  25    30    ->  2    ->   func/kwargs from meta[2]
        #   nan  25    nan   ->  1    ->   func/kwargs from meta[1]
        #   nan  nan   nan   ->  nan  ->   set func/kwargs to empty values
        # RESULT:
        #    flag  func       kwargs
        #    30     "flagBar"  {kw3: v3, kw4: v4, ...}
        #    25     "flagFoo"  {kw1: v1, kw2: v2, ...}
        #    nan    ""         {}
        def map_meta(i, meta) -> pd.Series:
            if pd.isna(i):
                return pd.Series({"func": "", "kwargs": {}})
            m = meta[int(i)]
            return pd.Series({"func": m.get("func", ""), "kwargs": m.get("kwargs", {})})

        meta_idx = history.hist.astype(float).agg(pd.Series.last_valid_index, axis=1)
        return meta_idx.apply(map_meta, meta=history.meta)

    def toExternal(self, flags: Flags, attrs: dict | None = None) -> DictOfSeries:
        """
        Returns a DictOfSeries with elements of type pd.Dataframe with
        the following columns:
         - flag: float - the float quality label
         - func: str - name of last applied function (might be empty str)
         - kwargs: dict - kwargs of last applied function (might be empty)

        For unflagged data points (no saqc quality function set a flag) the
        flag will be `saqc.UNFLAGGED`. The corresponding func and kwargs will
        be empty.
        """
        tflags = super().toExternal(flags, attrs)
        out = DictOfSeries()
        columns = pd.Index(["flag", "func", "kwargs"])
        for key, value in tflags.items():
            if tflags[key].empty:
                out[key] = pd.DataFrame(index=tflags[key].index, columns=columns)
                continue
            df = self.get_meta_per_row(flags.history[key])
            df["flag"] = tflags[key].fillna(saqc.UNFLAGGED)
            out[key] = df[columns].copy()  # reorder
        return out


class QualityControl:
    conn: Connection
    api_url: str
    proj: feta.Project
    schema: str
    conf: feta.QAQC
    tests: list[feta.QAQCTest]
    window: pd.Timedelta | int
    legacy: bool

    def __init__(
        self,
        conn: Connection,
        dbapi_url: str,
        project: feta.Project,
        qc_config: feta.QAQC,
    ):
        self.conn: Connection = conn
        self.api_url = dbapi_url
        self.proj = project
        self.conf = qc_config
        self.schema = self.proj.database.schema
        self.tests = self.conf.get_tests()
        self.window = self.parse_ctx_window(self.conf.context_window)
        self.legacy = any((t.position is not None) for t in self.tests)
        self.alias_map = {}

    @classmethod
    def from_project(
        cls,
        conn: Connection,
        dbapi_url: str,
        uuid: str,
        config_name: str | None = None,
    ):
        proj = feta.Project.from_uuid(uuid, dsn=conn)
        if config_name is None:
            if (qc := proj.get_default_qaqc()) is None:
                raise NoDataWarning(
                    f"No active QC-Settings found in project {proj.name}"
                )
        else:
            if not (qcs := proj.get_qaqcs(name=config_name)):
                raise DataNotFoundError(
                    f"No QC-Settings with name {config_name} "
                    f"found in project {proj.name}"
                )
            qc = qcs[0]
        return cls(conn, dbapi_url, proj, qc)

    @classmethod
    def from_thing(cls, conn: Connection, dbapi_url: str, uuid: str):
        thing = feta.Thing.from_uuid(uuid, dsn=conn)
        proj = thing.project
        qc = proj.get_default_qaqc() or thing.get_legacy_qaqc()
        if qc is None:
            raise NoDataWarning(
                f"Neither found active QC-Settings in the project {proj.name}, "
                f"nor legacy QC-Settings are found with the thing {thing.name}."
            )
        return cls(conn, dbapi_url, proj, qc)

    @staticmethod
    def extract_data_by_result_type(df: pd.DataFrame) -> pd.Series:
        """Selects the column, specified as integer in the column 'result_type'."""
        if df.empty:
            return pd.Series(index=df.index, dtype=float)
        dtype_mapping = {
            "result_type": NotImplemented,
            "result_number": float,
            "result_string": str,
            "result_boolean": bool,
            "result_json": object,
        }
        columns = pd.Index(dtype_mapping.keys())
        df = df[columns].copy(deep=False)

        # If we have a single result-type we can map a matching dtype
        if len(rt := df["result_type"].value_counts()) == 1:
            column = columns[rt.index[0] + 1]
            return df[column].astype(dtype_mapping[column])

        # We can't use raw=True (numpy-speedup) because the numpy arrays
        # don't always preserve the dtype. E.g. a bool might be cast
        # to float if another value is a float.
        return df.apply(lambda row: row.iloc[1 + row.iloc[0]], axis=1)

    @staticmethod
    def parse_ctx_window(window: int | str) -> pd.Timedelta | int:
        """Parse the `context_window` value of the config."""
        if isinstance(window, int) or isinstance(window, str) and window.isnumeric():
            window = int(window)
            is_negative = window < 0
        else:
            window = pd.Timedelta(window)
            is_negative = window.days < 0

        if is_negative:
            raise UserInputError(
                "Parameter 'context_window' must not have a negative value"
            )
        return window

    def fetch_thing_uuid_from_sta_id(self, thing_id: int) -> str | None:
        q = (
            "select thing_id as thing_uuid from public.sms_datastream_link l "
            "join public.sms_device_mount_action a on l.device_mount_action_id = a.id "
            "where a.configuration_id = %s"
        )
        row = self.conn.execute(cast(Literal, q), [thing_id]).fetchone()
        if row is None:
            raise DataNotFoundError(f"No thing_uuid for STA.Thing.Id {thing_id}")
        return row[0]

    def fetch_thing_uuid_for_sta_stream(self, sta_stream_id: int):
        q = (
            "select thing_id as thing_uuid from public.sms_datastream_link "
            "where device_property_id = %s"
        )
        row = self.conn.execute(cast(Literal, q), [sta_stream_id]).fetchone()
        if row is None:
            raise DataNotFoundError(
                f"No thing_uuid for STA.Datastream.Id {sta_stream_id}"
            )
        return row

    def fetch_datastream_by_pos(self, thing_uuid, position) -> dict[str, Any]:
        query = (
            "SELECT ds.id, ds.name, ds.position, ds.thing_id "
            "FROM {schema}.datastream ds "
            "JOIN {schema}.thing t ON t.id = ds.thing_id "
            "WHERE t.uuid = %s "
            "AND ds.position = %s"
        )
        # Note that 'position' is of type varchar in DB
        with self.conn.cursor(row_factory=dict_row) as cur:
            return cur.execute(
                sql.SQL(cast(Literal, query)).format(
                    schema=sql.Identifier(self.schema)
                ),
                [thing_uuid, str(position)],
            ).fetchone()

    def fetch_datastream_data_legacy(
        self,
        datastream_id: int,
        start_date: TimestampT | None,
        end_date: TimestampT | None,
        window: pd.Timedelta | int | None,
    ) -> list[DbRowT] | None:

        # (start_date - window) <= start_date <= data <= end_date
        # [===context window===]+[===============data============]
        if isinstance(window, pd.Timedelta) and start_date is not None:
            start_date = start_date - window
        if start_date is None:
            start_date = "-Infinity"
        if end_date is None:
            end_date = "Infinity"

        query = sql.SQL(
            cast(
                Literal,
                "select {fields} from {schema}.observation o "
                "where o.datastream_id = %s "
                "and o.result_time >= %s "
                "and o.result_time <= %s "
                "order by o.result_time desc "
                "limit %s",
            )
        ).format(
            fields=sql.SQL(", ").join(map(sql.Identifier, _OBS_COLUMNS)),
            schema=sql.Identifier(self.schema),
        )

        # Fetch data by dates including context window, iff it was defined
        # as a timedelta. None as limit, becomes SQL:'LIMIT NULL' which is
        # equivalent to 'LIMIT ALL'.
        params = [datastream_id, start_date, end_date, None]
        data = self.conn.execute(query, params).fetchall()
        if not data:  # If we have no data we also need no context data
            return None

        # Fetch data from context window, iff it was passed as a number,
        # which means number of observations before the actual data.
        context = []
        if isinstance(window, int) and window > 0:
            params = [datastream_id, "-Infinity", start_date, window]
            context = self.conn.execute(query, params).fetchall()
            # If the exact start_date is present in the data, the usage
            # of `>=` and `<=` will result in a duplicate row.
            if len(context) > 0 and context[0][0] == data[-1][0]:
                context = context[1:]

        # In the query we ordered descending (newest first) to correctly
        # use the limit keyword, but for python/pandas etc. we want to
        # return an ascending (oldest first) data set.
        return context[::-1] + data[::-1]

    def fetch_datastream_data_sta(
        self,
        sta_stream_id: int,
        start_date: TimestampT | None,
        end_date: TimestampT | None,
        window: pd.Timedelta | int | None,
    ) -> list[DbRowT] | None:

        # (start_date - window) <= start_date <= data <= end_date
        # [===context window===]+[===============data============]
        if isinstance(window, pd.Timedelta) and start_date is not None:
            start_date = start_date - window
        if start_date is None:
            start_date = "-Infinity"
        if end_date is None:
            end_date = "Infinity"

        # Mind that o."DATASTREAM_ID" is the STA datastream id
        query = sql.SQL(
            cast(
                Literal,
                "select {fields},  "
                "l.datastream_id as raw_datastream_id "
                'from {schema}."OBSERVATIONS" o '
                "join public.sms_datastream_link l "
                'on o."DATASTREAM_ID" = l.device_property_id '
                'where o."DATASTREAM_ID" = %s '
                'and o."RESULT_TIME" >= %s '
                'and o."RESULT_TIME" <= %s '
                'order by o."RESULT_TIME" desc '
                "limit %s",
            )
        ).format(
            fields=sql.SQL(", ").join(
                map(sql.Identifier, map(str.upper, _OBS_COLUMNS))
            ),
            schema=sql.Identifier(self.schema),
        )

        # Fetch data by dates including context window, iff it was defined
        # as a timedelta. None as limit, becomes SQL:'LIMIT NULL' which is
        # equivalent to 'LIMIT ALL'.
        params = [sta_stream_id, start_date, end_date, None]
        data = self.conn.execute(query, params).fetchall()
        if not data:  # If we have no data we also need no context data
            return None

        # Fetch data from context window, iff it was passed as a number,
        # which means number of observations before the actual data.
        context = []
        if isinstance(window, int) and window > 0:
            params = [sta_stream_id, "-Infinity", start_date, window]
            context = self.conn.execute(query, params).fetchall()
            # If the exact start_date is present in the data, the usage
            # of `>=` and `<=` will result in a duplicate row.
            if len(context) > 0 and context[0][0] == data[-1][0]:
                context = context[1:]

        # In the query we ordered descending (newest first) to correctly
        # use the limit keyword, but for python/pandas etc. we want to
        # return an ascending (oldest first) data set.
        return context[::-1] + data[::-1]

    def fetch_unflagged_daterange_legacy(
        self, datastream_id
    ) -> tuple[TimestampT, TimestampT] | tuple[None, None]:
        """Returns (first aka. earliest, last) timestamp of unflagged data."""
        part = (
            "select o.result_time from {schema}.observation o "
            "where o.datastream_id = %s and "
            "(o.result_quality is null or o.result_quality = 'null'::jsonb)"
            "order by result_time {order} limit 1"
        )
        newest = sql.SQL(part).format(
            schema=sql.Identifier(self.schema), order=sql.SQL("desc")
        )
        oldest = sql.SQL(part).format(
            schema=sql.Identifier(self.schema), order=sql.SQL("asc")
        )
        query = sql.SQL("({}) UNION ALL ({}) ORDER BY result_time").format(
            oldest, newest
        )
        r = self.conn.execute(query, [datastream_id, datastream_id]).fetchall()
        if not r:
            return None, None
        return r[0][0], r[1][0]

    def fetch_unflagged_daterange_sta(
        self, sta_stream_id
    ) -> tuple[TimestampT, TimestampT] | tuple[None, None]:
        """Returns (first aka. earliest, last) timestamp of unflagged data."""

        # Mind that o."DATASTREAM_ID" is the STA datastream id
        part = """\
            select o."RESULT_TIME" from {schema}."OBSERVATIONS" o 
            where o."DATASTREAM_ID" = %s and 
            (o."RESULT_QUALITY" is null or o."RESULT_QUALITY" = 'null'::jsonb)
            order by "RESULT_TIME" {order} limit 1
        """
        newest = sql.SQL(part).format(
            schema=sql.Identifier(self.schema), order=sql.SQL("desc")
        )
        oldest = sql.SQL(part).format(
            schema=sql.Identifier(self.schema), order=sql.SQL("asc")
        )
        query = sql.SQL('({}) UNION ALL ({}) ORDER BY "RESULT_TIME"').format(
            oldest, newest
        )
        r = self.conn.execute(query, [sta_stream_id, sta_stream_id]).fetchall()
        if not r:
            return None, None
        return r[0][0], r[1][0]

    def qaqc_legacy(self, thing_uuid) -> tuple[saqc.SaQC, dict[str, pd.DataFrame]]:
        """
        Returns a tuple of data in saqc.SaQC and a metadata dict.

        For each raw data (in contrast to derived data products) the
        metadata dict contains a pd.Dataframe (DF).

        The DF id indexed with the timestamps of the data. Note that the
        context window is not part of this index.
        The columns of the DF are:
         - 'thing_uuid': thing_uuid of the data point at this index
         - 'datastream_id': datastream id of the data point at this index
        """

        def fetch_data(pos) -> tuple[pd.Series, pd.DataFrame]:
            ds = self.fetch_datastream_by_pos(thing_uuid, pos)
            earlier, later = self.fetch_unflagged_daterange_legacy(ds["id"])
            obs = None
            if earlier is not None:  # else no unflagged data
                obs = self.fetch_datastream_data_legacy(
                    ds["id"], earlier, later, self.window
                )
            df = pd.DataFrame(obs or [], columns=_OBS_COLUMNS)
            df = df.set_index("result_time", drop=True)
            df.index = pd.DatetimeIndex(df.index)
            data = self.extract_data_by_result_type(df)
            # we truncate the context window
            if data.empty:
                data_index = data.index
            else:
                data_index = data.index[data.index.slice_indexer(earlier, later)]
            meta = pd.DataFrame(index=data_index)
            meta.attrs = {"repr_name": f"Datastream {ds['name']} of Thing {thing_uuid}"}
            meta["thing_uuid"] = thing_uuid
            meta["datastream_id"] = ds["id"]
            return data, meta

        qc = saqc.SaQC(scheme=KwargsScheme())
        md = dict()  # metadata
        for i, test in enumerate(self.tests):
            test: feta.QAQCTest
            origin = f"QA/QC Test #{i+1}: {self.conf.name}/{test.name}"

            # Raise for bad function, before fetching all the data
            attr = test.function
            try:
                func = getattr(qc, attr)
            except AttributeError:
                raise UserInputError(f"{origin}: Unknown SaQC function {attr}")

            kwargs: dict = (test.args or {}).copy()
            if (position := test.position) is not None:
                if (name := str(position)) not in qc:
                    data, meta = fetch_data(position)
                    qc[name] = data
                    md[name] = meta
                if "field" in kwargs:
                    logger.warning(
                        "argument 'field' is ignored and will be overwritten, "
                        "if legacy position is also given."
                    )
                kwargs["field"] = name

            # run QC
            try:
                qc = func(**kwargs)
            except Exception as e:
                raise UserInputError(
                    f"{origin}: Execution of test failed, because {e}"
                ) from e

        return qc, md

    def _fetch_sta_data(self, thing_id: int, stream_id, start_date, end_date):
        if start_date is None:
            earlier, later = self.fetch_unflagged_daterange_sta(stream_id)
        else:
            earlier, later = start_date, end_date

        thing_uuid = self.fetch_thing_uuid_for_sta_stream(stream_id)
        obs = []
        if earlier is not None:  # else: we have no unflagged data
            obs = self.fetch_datastream_data_sta(stream_id, earlier, later, self.window)
        df = pd.DataFrame(obs, columns=_OBS_COLUMNS + ["raw_datastream_id"])
        df = df.set_index("result_time", drop=True)
        df.index = pd.DatetimeIndex(df.index)
        data = self.extract_data_by_result_type(df)
        # we truncate the context window
        if data.empty:
            data_index = data.index
        else:
            data_index = data.index[data.index.slice_indexer(earlier, later)]
        meta = pd.DataFrame(index=data_index)
        meta.attrs = {"repr_name": f"Datastream {stream_id} of Thing {thing_id}"}
        meta["thing_uuid"] = thing_uuid
        meta["datastream_id"] = df["raw_datastream_id"]
        return data, meta

    def qaqc_sta(
        self,
        start_date: pd.Timestamp | None,
        end_date: pd.Timestamp | None,
    ) -> tuple[saqc.SaQC, dict[str, pd.DataFrame]]:

        qc = saqc.SaQC(scheme=KwargsScheme())
        md = dict()  # metadata

        for i, test in enumerate(self.tests):  # type: int, feta.QAQCTest
            origin = f"QA/QC Test #{i+1}: {self.conf.name}/{test.name}"
            kwargs: dict = (test.args or {}).copy()

            # Better raise for an unknown function, before we are fetching data
            if (func := getattr(qc, test.function, None)) is None:
                raise UserInputError(f"{origin}: Unknown SaQC function {test.function}")

            for stream in test.streams or []:  # type: feta.QcStreamT
                # add alias to kwargs, e.g. {"field": "T55S3"}
                tid = stream["sta_thing_id"]
                sid = stream["sta_stream_id"]
                alias = stream["alias"]
                self.alias_map[alias] = (tid, sid)
                dict_update_to_list(kwargs, stream["arg_name"], alias)
                if tid is None or sid is None or alias in qc:
                    # Either we've got a references to a temporary alias (tid is None)
                    # OR the user wants to create a new datastream on an existing
                    # thing (sid is None) OR we already fetched the data in a previous
                    # test (alias in qc).
                    continue
                data, meta = self._fetch_sta_data(tid, sid, start_date, end_date)
                qc[alias] = data
                md[alias] = meta
            try:
                qc = func(**kwargs)
            except Exception as e:
                raise UserInputError(
                    f"{origin}: Execution of test failed, because of {e}"
                ) from e

        return qc, md

    def run(self, start_date: str | None = None, end_date: str | None = None):
        """
        Run QA/QC on data in the Observation-DB and returns
        the number of observation that was updated.
        """
        if not self.tests:
            raise NoDataWarning(
                f"No quality functions present in config {self.conf.name!r}",
            )
        start_date = timestamp_from_string(start_date)
        end_date = timestamp_from_string(end_date)
        self.alias_map = {}
        qc, meta = self.qaqc_sta(start_date, end_date)
        # ============= dataproducts =============
        # Data products must be created before quality labels are uploaded.
        # If we first do the upload and an error occur we will not be able to
        # recreate the same data for the dataproducts, this is because a
        # qc run always just sees unflagged data.
        n = 0
        if dp_columns := [c for c in qc.columns if c not in meta.keys()]:
            n += self._create_dataproducts(qc[dp_columns])
        m = self._upload(qc, meta)
        return m

    def run_legacy(self, thing_uuid):
        """
        Run QA/QC on data in the Observation-DB for a single Thing.

        Returns the number of observation that was updated and/or created.
        """
        logger.info(f"Execute qaqc config {self.conf.name!r}")
        qc, meta = self.qaqc_legacy(thing_uuid)
        # ============= legacy dataproducts =============
        # Data products must be created before quality labels are uploaded.
        # If we first do the upload and an error occur we will not be able to
        # recreate the same data for the dataproducts, this is because a
        # legacy qc run always just sees unflagged data.
        n = 0
        if dp_columns := [c for c in qc.columns if c not in meta.keys()]:
            n += self._create_dataproducts_legacy(thing_uuid, qc[dp_columns])

        m = self._upload(qc, meta)
        return n + m

    def _upload(self, qc: saqc.SaQC, meta: dict[str, pd.DataFrame]):
        total = 0
        flags = qc.flags  # implicit flags translation  -> KwargsScheme
        for name in flags.columns:
            if name not in meta.keys():
                # Data products were already handled.
                continue
            repr_name = meta[name].attrs["repr_name"]
            flags_frame: pd.DataFrame = flags[name]
            flags_frame["flag"] = flags_frame["flag"].fillna(saqc.UNFLAGGED)

            # remove context window
            flags_frame = flags_frame.reindex(meta[name]["thing_uuid"].index)
            if flags_frame.empty:
                logger.debug(f"no new quality labels for {repr_name}")
                continue

            flags_frame["thing_uuid"] = meta[name]["thing_uuid"]
            flags_frame["datastream_id"] = meta[name]["datastream_id"]

            for uuid, group in flags_frame.groupby("thing_uuid", sort=False):
                labels = self._create_quality_labels(group, self.conf.id)

                try:
                    self._upload_quality_labels(uuid, labels)
                except requests.HTTPError as e:
                    if logger.isEnabledFor(logging.DEBUG):
                        detail = e.response.json().get("detail", None)
                        if isinstance(detail, list):
                            detail = "\n  ".join(str(d) for d in detail)
                        logger.debug(f"Error Detail:\n  {detail}")
                    raise RuntimeError(
                        f"uploading quality labels for variable {repr_name} failed"
                    ) from e

                logger.debug(f"uploaded {len(labels)} quality labels for {repr_name}")
                total += len(labels)

        return total

    def _upload_quality_labels(self, thing_uuid, qlabels: list[JsonObjectT]):
        r = requests.post(
            f"{self.api_url}/observations/qaqc/{thing_uuid}",
            json={"qaqc_labels": qlabels},
            headers={"Content-type": "application/json"},
        )
        r.raise_for_status()

    def _upload_dataproduct(self, thing_uuid, obs: list[JsonObjectT]):
        r = requests.post(
            f"{self.api_url}/observations/upsert/{thing_uuid}",
            json={"observations": obs},
            headers={"Content-type": "application/json"},
        )
        r.raise_for_status()

    @staticmethod
    def _create_quality_labels(flags_df: pd.DataFrame, config_id) -> list[JsonObjectT]:

        def compose_json(row: pd.Series) -> JsonObjectT:
            # The series has the following index labels:
            #  'flag': the quality flag/label
            #  'func': the function name that applied the flag
            #  'kwargs': the kwargs that was passed to the function
            #  'datastream_id': the datastream ID of the data
            # maybe more columns for internal use
            return {
                "result_time": row.name.isoformat(),  # noqa, index label
                "datastream_id": row["datastream_id"],
                "result_quality": json.dumps(
                    {
                        "annotation": str(row["flag"]),
                        "annotationType": "SaQC",
                        "properties": {
                            "version": saqc.__version__,
                            "measure": row["func"],
                            "configuration": config_id,
                            "userLabel": row["kwargs"].get("label", None),
                        },
                    }
                ),
            }

        return flags_df.apply(compose_json, axis=1).to_list()

    @staticmethod
    def _create_dataproduct(df: pd.DataFrame, name, config_id) -> list[JsonObjectT]:
        assert pd.Index(["data", "flag", "func", "kwargs"]).difference(df.columns).empty

        if pd.api.types.is_numeric_dtype(df["data"]):
            result_type = ObservationResultType.Number
            result_field = "result_number"
        elif pd.api.types.is_string_dtype(df["data"]):
            result_type = ObservationResultType.String
            result_field = "result_string"
        elif pd.api.types.is_bool_dtype(df["data"]):
            result_type = ObservationResultType.Bool
            result_field = "result_bool"
        elif pd.api.types.is_object_dtype(df["data"]):
            result_type = ObservationResultType.Json
            result_field = "result_json"
        else:
            raise UserInputError(f"data of type {df['data'].dtype} is not supported")

        def compose_json(row: pd.Series) -> JsonObjectT:
            val = row["data"]
            if result_type == ObservationResultType.Json:
                val = json.dumps(val)
            return {
                "result_time": row.name.isoformat(),  # noqa, index label
                "result_type": result_type,
                result_field: val,
                "result_quality": json.dumps(
                    {
                        "annotation": str(row["flag"]),
                        "annotationType": "SaQC",
                        "properties": {
                            "version": saqc.__version__,
                            "measure": row["func"],
                            "configuration": config_id,
                            "userLabel": row["kwargs"].get("label", None),
                        },
                    }
                ),
                "datastream_pos": name,
            }

        valid = df["data"].notna()
        return df[valid].apply(compose_json, axis=1).dropna().to_list()

    def _create_dataproducts(self, qc):
        total = 0
        flags, data = qc.flags, qc.data  # implicit flags translation ->KwargsScheme
        for name in flags.columns:
            tid, sid = self.alias_map.get(name, (None, None))
            if tid is None:
                # We've got a temporary dataproduct (TEMP.SomeStreamName),
                # which we don't upload.
                continue
            tid: int
            assert sid is None
            thing_uuid = self.fetch_thing_uuid_from_sta_id(tid)
            stream_name = name.split("S", maxsplit=1)[1]  # T23SuserGivenName
            df: pd.DataFrame = flags[name]
            df["data"] = data[name]
            if df.empty:
                logger.debug(f"no data for data product {name}")
                continue
            obs = self._create_dataproduct(df, stream_name, self.conf.id)
            self._upload_dataproduct(thing_uuid, obs)
            logger.info(f"uploaded {len(obs)} data points for dataproduct {name!r}")
            total += len(obs)
        return total

    def _create_dataproducts_legacy(self, thing_uuid, qc):
        total = 0
        flags, data = qc.flags, qc.data  # implicit flags translation ->KwargsScheme
        for name in flags.columns:
            df: pd.DataFrame = flags[name]
            df["data"] = data[name]
            if df.empty:
                logger.debug(f"no data for data product {name}")
                continue
            obs = self._create_dataproduct(df, name, self.conf.id)
            self._upload_dataproduct(thing_uuid, obs)
            logger.info(f"uploaded {len(obs)} data points for dataproduct {name!r}")
            total += len(obs)
        return total
