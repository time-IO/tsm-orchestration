#!/usr/bin/env python3
import psycopg
import saqc

from timeio import feta
from timeio.qc.datastream import Datastream, ProductStream, LocalStream

import typing

from timeio.qc.qctools import QcTool

if typing.TYPE_CHECKING:
    from timeio.qc.qctest import QcTest, StreamInfo, QcResult


class StreamManager:
    """
    The stream manager holds a collection of (data-) streams.

    It creates and stores streams from a stream's name and STA IDs.
    The streams can be used to retrieve data from the observation
    database (input/download).
    A stream can also store data and/or quality labels which can be
    later synced back to the database (output/upload).
    """
    def __init__(self, db_conn: psycopg.Connection) -> str:
        self._streams: dict[str, Datastream] = {}
        self._conn = db_conn

    def get_stream_schema(self, sta_thing_id):
        if sta_thing_id is None:
            return None

        query = (
            "select thing_id as thing_uuid from public.sms_datastream_link l "
            "join public.sms_device_mount_action a on l.device_mount_action_id = a.id "
            "where a.configuration_id = %s"
        )
        with self._conn.cursor() as cur:
            row = cur.execute(query, [sta_thing_id]).fetchone()
        thing_uuid = row[0]
        return feta.Thing.from_uuid(thing_uuid, self._conn).database.schema

    def add_stream(self, stream_info: StreamInfo):
        tid = stream_info.thing_id
        sid = stream_info.stream_id
        name = stream_info.value
        schema = self.get_stream_schema(tid, sid)

        if stream_info.is_dataproduct:
            new = ProductStream(tid, sid, name, self._conn, schema)
        elif stream_info.is_temporary:
            new = LocalStream(tid, sid, name, self._conn, schema)
        else:
            new = Datastream(tid, sid, name, self._conn, schema)

        self._streams[name] = new

    def get_stream(self, stream_info: StreamInfo):
        name = stream_info.value
        if name not in self._streams:
            self.add_stream(stream_info)
        return self._streams[name]

    def update(self, result: QcResult):
        """ Update streams with new data and/or quality labels. """
        for name in result.columns:
            if name not in self._streams:
                self._streams[name] = LocalStream(None, None, name, None, None)

            stream = self._streams[name]

            # Dataproducts and temporary variables.
            qlabels = result.quality[name]
            if isinstance(stream, (ProductStream, LocalStream)):
                data = result.data[name]
                stream.set_data(data, qlabels)

            # Regular quality labels for existing data.
            else:
                stream.update_quality_labels(qlabels)

    def upload(self):
        for stream in self._streams.values():
            # Data from a local stream (aka a temporary
            # variable) is not intended to be uploaded.
            if isinstance(stream, LocalStream):
                continue
            stream.upload()
