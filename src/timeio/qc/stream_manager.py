#!/usr/bin/env python3
import psycopg
import saqc

from timeio import feta
from timeio.qc.datastream import Datastream, ProductStream, LocalStream

import typing

if typing.TYPE_CHECKING:
    from timeio.qc.qctest import QcTest, StreamParam


class StreamManager:
    """
    Handle IO streams for QC.
    This includes fetching data from the DB for input streams
    and uploading results via the DB-API for output streams.

    The data is cached and more data (including overlaps) are
    supported.
    """
    def __init__(self, db_conn: psycopg.Connection) -> str:
        self._streams: dict[str, Datastream] = {}
        self._conn = db_conn

    def get_stream_schema(self, thing_id, stream_id):
        query = (
            "select thing_id as thing_uuid from public.sms_datastream_link l "
            "join public.sms_device_mount_action a on l.device_mount_action_id = a.id "
            "where a.configuration_id = %s"
        )
        with self._conn.cursor() as cur:
            row = cur.execute(query, [self.thing_id]).fetchone()
        thing_uuid = row[0]
        return feta.Thing.from_uuid(thing_uuid, self._conn).database.schema

    def add_stream(self, stream_info: StreamParam):
        tid = stream_info.thing_id
        sid = stream_info.stream_id
        name = stream_info.value

        schema = self.get_stream_schema(tid, sid)

        if stream_info.is_dataproduct:
            klass = ProductStream
        elif stream_info.is_temporary:
            klass = LocalStream
        else:
            klass = Datastream

        self._streams[name] = klass(tid, sid, name, self._conn, schema)

    def get_stream(self, stream_info: StreamParam):
        name = stream_info.value
        if name not in self._streams:
            self.add_stream(stream_info)
        return self._streams[name]

    def update(self, result):
        for name in result:
            if name not in self._streams:
                self._streams[name] = LocalStream(None, None, name, None, None)

            stream = self._streams[name]
            if isinstance(stream, (ProductStream, LocalStream)):
                stream.set_data(result.data[name], result.flags[name])
            else:
                stream.update_quality_labels(result.flags[name])

    def upload(self):
        for stream in self._streams.values():
            # Data from a local stream (aka a temporary
            # variable) is not intended to be uploaded.
            if isinstance(stream, LocalStream):
                continue
            stream.upload()
