#!/usr/bin/env python3

from datetime import datetime, timezone
from unittest.mock import Mock, call

import pytest
from minio.datatypes import Object

from run_file_ingest import ParserJobHandler


@pytest.mark.parametrize("has_exact_match", [True, False])
def test_parser_tags_only_reads_exact_filename_versions(has_exact_match):
    handler = ParserJobHandler.__new__(ParserJobHandler)
    handler.minio = Mock()
    versions = [
        Object(
            "bucket",
            "file.DBD.bak",
            version_id="other-file",
            last_modified=datetime(2026, 1, 3, tzinfo=timezone.utc),
        )
    ]
    if has_exact_match:
        versions.extend(
            Object(
                "bucket",
                "file.DBD",
                version_id=version_id,
                last_modified=datetime(2026, 1, day, tzinfo=timezone.utc),
            )
            for version_id, day in [("old", 1), ("new", 2)]
        )
    handler.minio.list_objects.return_value = iter(versions)
    tags = {"parsing_status": "successful", "parser_id": "parser"}
    handler.minio.get_object_tags.side_effect = [
        {"parsing_status": "failed"},
        tags,
    ]

    result = handler.get_parser_tags("bucket", "file.DBD")

    if has_exact_match:
        assert result == tags
        assert handler.minio.get_object_tags.call_args_list == [
            call("bucket", "file.DBD", version_id="new"),
            call("bucket", "file.DBD", version_id="old"),
        ]
    else:
        assert result is None
        handler.minio.get_object_tags.assert_not_called()


@pytest.mark.parametrize(
    "content, expected",
    [
        ({"EventName": "s3:something"}, False),
        ({"EventName": "s3:ObjectCreated:Put"}, True),
        ({"EventName": "s3:ObjectCreated:CompleteMultipartUpload"}, True),
    ],
)
def test__ParserJobHandler_is_valid_event(content, expected):
    result = ParserJobHandler.is_valid_event(content)
    assert result == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ({}, KeyError("EventName")),
        (None, TypeError(".* object is not subscriptable$")),
        (99, TypeError(".* object is not subscriptable$")),
    ],
)
def test__ParserJobHandler_is_valid_event__raises(content, expected):
    with pytest.raises(type(expected), match=str(expected)):
        ParserJobHandler.is_valid_event(content)
