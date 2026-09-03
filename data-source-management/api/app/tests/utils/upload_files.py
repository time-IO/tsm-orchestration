from __future__ import annotations

import csv
import io
import json
from datetime import timedelta, datetime
from typing import BinaryIO

from starlette.datastructures import UploadFile


def _csv_row(values: tuple[str, str, str]) -> str:
    buf = io.StringIO()
    csv.writer(buf).writerow(values)
    return buf.getvalue()


def make_csv_upload_file(
        size_bytes: int,
        *,
        columns: tuple[str, str, str] = ("col_a", "col_b", "col_c"),
        timestamp_column: int | None = 0,
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        timestamp_start: datetime = datetime(2024, 1, 1),
) -> UploadFile:
    parts = [_csv_row(columns)]
    total = len(parts[0].encode("utf-8"))
    i = 0
    while total < size_bytes:
        values = [f"{columns[0]}_{i}", f"{columns[1]}_{i}", f"{columns[2]}_{i}"]
        if timestamp_column is not None:
            values[timestamp_column] = (timestamp_start + timedelta(seconds=i)).strftime(timestamp_format)
        row = _csv_row(tuple(values))
        parts.append(row)
        total += len(row.encode("utf-8"))
        i += 1

    content = "".join(parts).encode("utf-8")
    return UploadFile(file=io.BytesIO(content), filename="tmp.csv")


def make_json_upload_file(
        size_bytes: int,
        *,
        filename: str = "test.json",
        keys: tuple[str, str, str] = ("key_a", "key_b", "key_c"),
        timestamp_key: str | None = "timestamp",
        timestamp_format: str = "%Y-%m-%dT%H:%M:%S",
        timestamp_start: datetime = datetime(2024, 1, 1),
) -> UploadFile:
    comma_byte_size = 1
    brackets_byte_size = 2
    entries = []
    i = 0
    total_byte_size = brackets_byte_size
    while total_byte_size < size_bytes:
        entry = {k: f"{k}_{i}" for k in keys}
        if timestamp_key is not None:
            entry[timestamp_key] = (timestamp_start + timedelta(seconds=i)).strftime(timestamp_format)
        entry_bytes = len(json.dumps(entry, separators=(",", ":")).encode("utf-8"))
        total_byte_size += entry_bytes + (comma_byte_size if entries else 0)
        entries.append(entry)
        i += 1

    content = json.dumps(entries, separators=(",", ":")).encode("utf-8")
    return UploadFile(file=io.BytesIO(content), filename=filename)


def as_multipart_file(
        upload_file: UploadFile,
        *,
        content_type: str = "application/octet-stream",
) -> tuple[str | None, BinaryIO, str]:
    upload_file.file.seek(0)
    return upload_file.filename, upload_file.file, content_type


def get_upload_file_size(upload_file: UploadFile) -> int:
    upload_file.file.seek(0, io.SEEK_END)
    size = upload_file.file.tell()
    upload_file.file.seek(0)
    return size
