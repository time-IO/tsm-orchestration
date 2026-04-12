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

    def convert_df(stream: QcFunctionStream, df: pd.DataFrame):
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
        return df

    def upload_full_streams(streams: dict[str, list]):

        out = []
        for thing_uuid, dfs in streams.items():
            df = pd.concat(dfs)

            # datastreams
            stream_names = (
                df.loc[df["datastream_id"].isnull(), "datastream_pos"]
                .drop_duplicates()
                .tolist()
            )
            if stream_names:
                # create newly generated datastreams
                datastreams = dbapi.insert_datastreams(
                    thing_uuid=thing_uuid,
                    datastreams=[{"datastream_pos": n} for n in stream_names],
                    mutable=True,
                )
                out.append(datastreams)

                # add ids
                df = (
                    df.merge(
                        pd.DataFrame(datastreams).rename(
                            columns={"id": "datastream_id"}
                        ),
                        left_on="datastream_pos",
                        right_on="position",
                        suffixes=("_x", "_y"),
                    )
                    .drop(columns="datastream_id_x")
                    .rename(columns={"datastream_id_y": "datastream_id"})
                )

            # observations
            observations = df.drop(columns="result_quality").to_dict(orient="records")
            dbapi.upsert_observations(thing_uuid=thing_uuid, observations=observations)

            # qaqc
            # labels = df[["result_time", "result_quality", "datastream_id"]]
            # TODO: refactor out and use upload_quality instead
            # dbapi.upsert_qc_labels(
            #     thing_uuid=thing_uuid, qc_labels=labels.to_dict(orient="records")
            # )
            # return out

    def upload_quality(streams: dict[str, list]):
        for thing_uuid, dfs in streams.items():
            df = pd.concat(dfs)
            labels = df[["result_time", "result_quality", "datastream_id"]]
            labels["result_quality"] = labels["result_quality"]

            import ipdb; ipdb.set_trace()
            dbapi.upsert_qc_labels(
                thing_uuid=thing_uuid, qc_labels=labels.to_dict(orient="records")
            )

    data_streams = defaultdict(list)
    qc_streams = defaultdict(list)

    for stream, df in qc.data.items():
        # TODO: simplify the outer case selection away, if possible
        if df.empty:
            continue
        converted = convert_df(stream, df)

        if stream.sta_stream_id is None:
            # we have a newly created datastream -> simply upload
            data_streams[stream.thing_uuid].append(converted)
        elif qc.data_is_modified(stream):
            if not stream.is_mutable:
                raise ImmutableDatastreamError(f"changes to immutable datatstream {stream} detected")
            if qc.index_is_modified(stream):
                dbapi.delete_observations(
                    stream.thing_uuid,
                    stream.datastream_name,
                    start_date=converted.index[0],
                    end_date=converted.index[-1],
                )
            data_streams[stream.thing_uuid].append(converted)
        # else:
        qc_streams[stream.thing_uuid].append(converted)

    streams = upload_full_streams(data_streams)
    upload_quality(qc_streams)
    import ipdb; ipdb.set_trace()


def read_stream_data(
    db_api: DBapi,
    streams: list[QcFunctionStream] | set[QcFunctionStream],
    start_date: pd.Timestamp = pd.Timestamp("1700-01-01", tz="UTC"),
    end_date: pd.Timestamp = pd.Timestamp("3000-12-11", tz="UTC"),
) -> dict[QcFunctionStream, pd.DataFrame]:

    # NOTE:
    # `start_date` and `end_date` are delivered by the parser via the
    # data_parsed message the worker-run-qaqc is listening to. Currently
    # there is still the possibility that the parsed timestamps are not
    # timezone aware, if this happens, the parser implictly choses local
    # time, for us 'Europe/Berlin'. In the future, we will enforce time
    # zone settings by users of the data-source-management, thus, we won't
    # run into issues with time zone awareness again.
    # TODO:
    # Remove the automatic timezone setting, as will result in incorrect
    # behavior, if time.IO is running under different timezone settings
    if start_date.tz is None:
        start_date = pd.Timestamp(start_date).tz_localize("Europe/Berlin")
    if end_date.tz is None:
        end_date = pd.Timestamp(end_date).tz_localize("Europe/Berlin")

    out = {}
    for stream in streams:
        if stream.db_stream_id:
            data = db_api.get_datastream_observations(
                stream.thing_uuid,
                stream.position,
                start_date=max(filter(None, [start_date, stream.start_date])),
                end_date=min(filter(None, [end_date, stream.end_date])),
            )

            df = pd.DataFrame(data["observations"])
            out[stream] = pd.DataFrame(
                data = {
                    "data": df.to_numpy()[
                        np.arange(len(df)), df["result_type"] + 2
                    ].astype(float),
                    "quality": df["result_quality"].astype(object),
                },
                index=pd.to_datetime(df["result_time"])
            )

    return out
