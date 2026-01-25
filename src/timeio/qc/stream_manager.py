#!/usr/bin/env python3
from __future__ import annotations
import typing

import logging

from requests import HTTPError

from timeio import feta
from timeio.errors import UploadError
from timeio.qc.datastream import (
    AbstractDatastream,
    AbstractDatastreamFactory,
    ProductStream,
    LocalStream,
)

if typing.TYPE_CHECKING:
    from timeio.qc.qctest import StreamInfo, QcResult

logger = logging.getLogger("StreamManager")


class StreamManager:
    """
    The stream manager holds a collection of (data-) streams.

    It creates and stores streams from a stream's name and STA IDs.
    The streams can be used to retrieve data from the observation
    database (input/download).
    A stream can also store data and/or quality labels which can be
    later synced back to the database (output/upload).
    """

    def __init__(self, stream_factory: AbstractDatastreamFactory):
        self._streams: dict[str, AbstractDatastream] = {}
        self._factory = stream_factory

    def add_stream(self, stream_info: StreamInfo):
        self._streams[stream_info.value] = self._factory.create(stream_info)

    def get_stream(self, stream_info: StreamInfo):
        name = stream_info.value
        if name not in self._streams:
            self.add_stream(stream_info)
        return self._streams[name]

    def update(self, result: QcResult):
        """Update streams with new data and/or quality labels."""

        for name in result.columns:
            if name not in self._streams:
                self._streams[name] = LocalStream(None, None, name, None, None)

            stream = self._streams[name]

            # Add new or modified data (e.g. for Dataproducts).
            if isinstance(stream, (ProductStream, LocalStream)):
                data = result.data[name]
                stream.set_data(data)

            # Set quality labels.
            qlabels = result.quality[name]
            stream.update_quality_labels(qlabels)

    def upload(self, api_base_url: str):
        for stream in self._streams.values():
            # Data from a local stream (aka a temporary
            # variable) is not intended to be uploaded.
            if isinstance(stream, LocalStream):
                continue

            try:
                stream.upload(api_base_url)
            except HTTPError as e:
                raise UploadError(f"Upload failed for stream {stream}") from e
            except Exception as e:
                e.add_note(f"Stream: {stream}")
                raise e

    def __repr__(self):
        streams = list(self._streams.values())
        return f"StreamManager({streams})"
