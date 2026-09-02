#!/usr/bin/env python3
"""Tests for the mtime range filtering of :func:`timeio.remote_fs.sync`."""

from __future__ import annotations

import io
from datetime import datetime, timezone

from timeio.remote_fs import RemoteFS, sync


def _epoch(value: str) -> float:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()


class FakeFS(RemoteFS):
    """In-memory RemoteFS. ``files`` maps path -> (size, mtime, is_dir)."""

    def __init__(self, files: dict[str, tuple[int, float, bool]] | None = None):
        self.files = files or {}

    def exist(self, path: str) -> bool:
        return path in self.files

    def is_dir(self, path: str) -> bool:
        return self.files[path][2]

    def last_modified(self, path: str) -> float:
        return self.files[path][1]

    def size(self, path: str) -> int:
        return self.files[path][0]

    def open(self, path: str):
        return io.BytesIO(b"")

    def put(self, path: str, fo, size: int) -> None:
        self.files[path] = (size, 0.0, False)

    def mkdir(self, path: str) -> None:
        self.files[path] = (0, 0.0, True)

    def close(self) -> None:
        pass


def _make_source() -> FakeFS:
    return FakeFS(
        {
            "old.txt": (1, _epoch("2020-01-01 00:00:00"), False),
            "mid.txt": (1, _epoch("2021-06-15 12:00:00"), False),
            "new.txt": (1, _epoch("2022-12-31 23:59:59"), False),
        }
    )


def test_sync_without_range_copies_all():
    src, trg = _make_source(), FakeFS()
    sync(src, trg, "thing-uuid", "sftp")
    assert set(trg.files) == {"old.txt", "mid.txt", "new.txt"}


def test_sync_with_lower_bound_only():
    src, trg = _make_source(), FakeFS()
    sync(src, trg, "thing-uuid", "sftp",datetime_from="2021-01-01 00:00:00")
    assert set(trg.files) == {"mid.txt", "new.txt"}


def test_sync_with_upper_bound_only():
    src, trg = _make_source(), FakeFS()
    sync(src, trg, "thing-uuid", "sftp", datetime_to="2021-01-01 00:00:00")
    assert set(trg.files) == {"old.txt"}


def test_sync_with_both_bounds():
    src, trg = _make_source(), FakeFS()
    sync(
        src,
        trg,
        "thing-uuid",
        "sftp",
        datetime_from="2021-01-01 00:00:00",
        datetime_to="2022-01-01 00:00:00",
    )
    assert set(trg.files) == {"mid.txt"}
