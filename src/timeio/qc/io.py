#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import typing
import json
from collections import defaultdict

import numpy as np
import pandas as pd

from timeio.common import ObservationResultType, get_result_field_name
from timeio.databases import DBapi

if typing.TYPE_CHECKING:
    from timeio.qc.saqc import SaQCWrapper
    from timeio.qc.qcfunction import QcFunctionStream

    StreamsT = dict[QcFunctionStream, pd.DataFrame]


logger = logging.getLogger("run-quality-control")


class ImmutableDatastreamError(Exception):
    pass


def get_result_type(data: pd.Series):
    # NOTE:
    # - That seems to be a lot of effort...
    # - I guess we do the same things at various
    #   places throughout the codebase
    if pd.api.types.is_numeric_dtype(data):
        return ObservationResultType.Number
    elif pd.api.types.is_string_dtype(data):
        return ObservationResultType.String
    elif pd.api.types.is_bool_dtype(data):
        return ObservationResultType.Bool
    elif pd.api.types.is_object_dtype(data):
        return ObservationResultType.Json
    else:
        raise ValueError(f"Data of type {data.dtype} is not supported.")


def write_qc_data(dbapi: DBapi, qc: SaQCWrapper):

    def prepare_dataframes(streams: StreamsT) -> StreamsT:
        out = {}
        for stream, df in streams.items():
            if df.empty:
                continue

            # trim context window away
            df = df.loc[df.index[0] + stream.context_window :]

            df["result_time"] = df.index.strftime("%Y-%m-%dT%H:%M:%S")
            df["result_type"] = rt = get_result_type(df["data"])
            df["datastream_id"] = stream.db_stream_id
            df["datastream_pos"] = stream.datastream_name
            columns_map = {
                "quality": "result_quality",
                "data": get_result_field_name(rt, errors="raise"),
            }
            df = df.rename(columns=columns_map)
            df["result_quality"] = df["result_quality"].map(json.dumps)

            out[stream] = df
        return out

    def setup_new_streams(streams: StreamsT) -> list[QcFunctionStream]:
        """
        setup all datastreams generated during the qc run
        """
        out = []
        for stream in streams.keys():
            if stream.sta_stream_id is None:
                datastreams = dbapi.insert_datastreams(
                    thing_uuid=stream.thing_uuid,
                    datastreams=[{"datastream_pos": stream.position}],
                    mutable=True,
                )
                stream.db_stream_id = int(datastreams[0]["id"])
                out.append(stream)
        return out

    def clear_modified_streams(streams: StreamsT) -> list[QcFunctionStream]:
        """
        check all modified data streams for validity and remove data if necessary
        """
        out = []
        for stream, df in streams.items():
            if qc.data_is_modified(stream):
                if not stream.is_mutable:
                    raise ImmutableDatastreamError(
                        f"changes to immutable datatstream '{stream.position}' detected"
                    )
                if qc.index_is_modified(stream):
                    dbapi.delete_observations(
                        stream.thing_uuid,
                        stream.datastream_name,
                        start_date=df.index[0],
                        end_date=df.index[-1],
                    )
                out.append(stream)
        return out

    def upload_data(streams: dict[str, pd.DataFrame]):
        for thing_uuid, df in streams.items():
            # observations
            observations = df.drop(columns="result_quality").to_dict(orient="records")
            dbapi.upsert_observations(thing_uuid=thing_uuid, observations=observations)

    def upload_quality(streams: dict[str, pd.DataFrame]):
        for thing_uuid, df in streams.items():
            labels = df[["result_time", "result_quality", "datastream_id"]]
            # labels["result_quality"] = labels["result_quality"]
            dbapi.upsert_qc_labels(
                thing_uuid=thing_uuid, qc_labels=labels.to_dict(orient="records")
            )

    def prepare_upload(streams: StreamsT) -> dict[str, pd.DataFrame]:
        tmp = defaultdict(list)
        for stream, df in streams.items():
            df["datastream_id"] = stream.db_stream_id
            tmp[stream.thing_uuid].append(df)
        return {uuid: pd.concat(dfs) for uuid, dfs in tmp.items()}

    streams = prepare_dataframes(qc.data)
    new_streams = setup_new_streams(streams)
    modified_streams = clear_modified_streams(streams)

    upload_data(
        prepare_upload(
            {s: df for s, df in streams.items() if s in new_streams + modified_streams}
        )
    )
    upload_quality(prepare_upload(streams))


def read_stream_data(
    db_api: DBapi,
    streams: list[QcFunctionStream] | set[QcFunctionStream],
    start_date: pd.Timestamp = pd.Timestamp("1717-01-01", tz="UTC"),
    end_date: pd.Timestamp = pd.Timestamp("2222-12-11", tz="UTC"),
) -> dict[QcFunctionStream, pd.DataFrame]:

    # NOTE:
    # `start_date` and `end_date` are delivered by the parser via the
    # data_parsed message the worker-run-qaqc is listening to. Currently
    # there is still the possibility that the parsed timestamps are not
    # timezone aware, if this happens, the parser implictly chooses local
    # time, for us 'Europe/Berlin'. In the future, we will enforce time
    # zone settings by users of the data-source-management, thus, we won't
    # run into issues with time zone awareness again.
    # TODO:
    # Remove the automatic timezone setting, as it will result in incorrect
    # behavior, if time.IO is running under different timezone settings
    if start_date.tz is None:
        start_date = pd.Timestamp(start_date).tz_localize("Europe/Berlin")
    if end_date.tz is None:
        end_date = pd.Timestamp(end_date).tz_localize("Europe/Berlin")

    out = {}
    for stream in streams:
        if stream.db_stream_id:
            start = max(filter(None, [start_date, stream.start_date]))
            end = min(filter(None, [end_date, stream.end_date]))
            data = db_api.get_datastream_observations(
                stream.thing_uuid,
                stream.position,
                start_date=start - stream.context_window,
                end_date=end,
            )

            df = pd.DataFrame(data["observations"])
            df = df[df.result_type == 0]
            out[stream] = pd.DataFrame(
                data={
                    "data": df.result_number.to_numpy(),
                    "quality": df.result_quality.to_numpy().astype(object)
                },
                index=pd.to_datetime(df["result_time"]),
            )

    return out
