#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from minio.error import S3Error

from timeio import reparse
from timeio.reparse import _to_utc, get_parse_info, reparse_files

UTC = timezone.utc


class FakeInfo:
    """Stand-in for paho's MQTTMessageInfo: indexable (rc, mid) + wait_for_publish."""

    def __init__(self, rc=0):
        self.rc = rc
        self.waited = False

    def __getitem__(self, index):
        return (self.rc, 1)[index]

    def wait_for_publish(self, timeout=None):
        self.waited = True


def tags(status, parser_id=None):
    t = {"parsing_status": status}
    if parser_id is not None:
        t["parser_id"] = parser_id
    return t


# name -> (last_modified, tags)
FILES = {
    "new.csv": (datetime(2026, 3, 1, tzinfo=UTC), None),
    "failed.csv": (datetime(2026, 3, 2, tzinfo=UTC), tags("failed", "OLD")),
    "done.csv": (datetime(2026, 3, 3, tzinfo=UTC), tags("successful", "OLD")),
    "other.txt": (datetime(2026, 3, 4, tzinfo=UTC), None),
}


class Env:
    def __init__(self, files):
        self.files = files
        self.thing = SimpleNamespace(
            uuid="THING",
            raw_data_storage=SimpleNamespace(bucket="bucket", filename_pattern="*.csv"),
            s3_store=SimpleNamespace(file_parser=SimpleNamespace(uuid="CURRENT")),
        )
        self.minio = MagicMock()
        self.minio.list_objects.return_value = [
            SimpleNamespace(object_name=name, last_modified=date)
            for name, (date, _) in files.items()
        ]
        self.minio.get_object_tags.side_effect = lambda bucket, name: files[name][1]
        self.publisher = MagicMock()
        self.publisher.publish.side_effect = lambda *a, **kw: FakeInfo()
        self.journal = MagicMock()
        self.parser_exists_calls = []

    def run(self, **kwargs):
        return reparse_files(
            self.thing, self.minio, self.publisher, self.journal, "dsn", **kwargs
        )

    def sent(self):
        """{file name: parser_uuid} of all published messages."""
        result = {}
        for call in self.publisher.publish.call_args_list:
            message = json.loads(call.args[1])
            result[message["Key"].split("/", 1)[1]] = message["parser_uuid"]
        return result


@pytest.fixture
def make_env(monkeypatch):
    def factory(files=None):
        env = Env(FILES if files is None else files)

        def parser_exists(uuid, dsn):
            env.parser_exists_calls.append(uuid)
            return uuid != "DELETED"

        monkeypatch.setattr(reparse, "parser_exists", parser_exists)
        return env

    return factory


def test_defaults_send_only_unparsed_files_with_current_parser(make_env):
    env = make_env()

    summary = env.run()

    # done.csv is already parsed, other.txt does not match the thing's pattern
    assert env.sent() == {"new.csv": "CURRENT", "failed.csv": "CURRENT"}
    assert (summary.published, summary.skipped, summary.failed) == (2, 0, 0)


def test_message_content_topic_and_qos(make_env):
    env = make_env()

    env.run()

    call = env.publisher.publish.call_args_list[0]
    assert call.args[0] == reparse.TOPIC
    assert call.kwargs["qos"] == 1
    assert json.loads(call.args[1]) == {
        "EventName": "s3:ObjectCreated:Put",
        "reparsing": True,
        "parser_uuid": "CURRENT",
        "Key": "bucket/new.csv",
    }


def test_include_parsed_uses_current_parser_by_default(make_env):
    env = make_env()

    env.run(include_parsed=True)

    # not the parser from the tag ("OLD")
    assert env.sent() == {
        "new.csv": "CURRENT",
        "failed.csv": "CURRENT",
        "done.csv": "CURRENT",
    }


def test_include_parsed_original_uses_parser_from_tag_for_parsed_files(make_env):
    env = make_env()

    env.run(include_parsed=True, parsed_files_parser="original")

    # unparsed files always get the current parser, parsed ones their original
    assert env.sent() == {
        "new.csv": "CURRENT",
        "failed.csv": "CURRENT",
        "done.csv": "OLD",
    }


def test_original_parser_deleted_skips_file_and_warns(make_env):
    files = {
        **FILES,
        "gone.csv": (datetime(2026, 3, 5, tzinfo=UTC), tags("successful", "DELETED")),
    }
    env = make_env(files)

    summary = env.run(include_parsed=True, parsed_files_parser="original")

    assert "gone.csv" not in env.sent()
    assert env.sent()["done.csv"] == "OLD"
    assert summary.skipped == 1
    env.journal.warning.assert_called_once()
    message, thing_uuid = env.journal.warning.call_args.args
    assert "gone.csv" in message and "DELETED" in message
    assert thing_uuid == "THING"


def test_original_parser_missing_in_tag_skips_file(make_env):
    files = {"x.csv": (datetime(2026, 3, 1, tzinfo=UTC), tags("successful"))}
    env = make_env(files)

    summary = env.run(include_parsed=True, parsed_files_parser="original")

    assert env.sent() == {}
    assert summary.skipped == 1
    env.journal.warning.assert_called_once()
    assert env.parser_exists_calls == []  # no lookup for an empty parser id


def test_parser_existence_is_checked_once_per_parser(make_env):
    files = {
        f"{n}.csv": (datetime(2026, 3, 1, tzinfo=UTC), tags("successful", "OLD"))
        for n in "abc"
    }
    env = make_env(files)

    env.run(include_parsed=True, parsed_files_parser="original")

    assert env.parser_exists_calls == ["OLD"]
    assert env.sent() == {"a.csv": "OLD", "b.csv": "OLD", "c.csv": "OLD"}


def test_explicit_parser_wins_for_all_files(make_env):
    files = {
        **FILES,
        "gone.csv": (datetime(2026, 3, 5, tzinfo=UTC), tags("successful", "DELETED")),
    }
    env = make_env(files)

    summary = env.run(
        parser_uuid="CHOSEN", include_parsed=True, parsed_files_parser="original"
    )

    assert set(env.sent().values()) == {"CHOSEN"}
    assert len(env.sent()) == 4  # new, failed, done, gone
    assert summary.skipped == 0
    env.journal.warning.assert_not_called()


def test_date_range_is_inclusive_and_naive_dates_are_utc(make_env):
    env = make_env()

    env.run(
        start_date="2026-03-02",
        end_date="2026-03-03 00:00:00",
        include_parsed=True,
    )

    # new.csv (03-01) is before start, other.txt is filtered by pattern,
    # failed.csv (03-02) and done.csv (03-03) sit exactly on the bounds
    assert set(env.sent()) == {"failed.csv", "done.csv"}


def test_extra_filename_pattern_narrows_selection(make_env):
    env = make_env()

    env.run(filename_pattern="new*", include_parsed=True)

    assert set(env.sent()) == {"new.csv"}


def test_tags_are_read_but_never_written(make_env):
    env = make_env()

    env.run(include_parsed=True, parsed_files_parser="original")

    env.minio.set_object_tags.assert_not_called()


def test_publish_failure_is_counted_and_not_awaited(make_env):
    env = make_env()
    infos = [FakeInfo(rc=4), FakeInfo(rc=0)]
    env.publisher.publish.side_effect = lambda *a, **kw: infos.pop(0)

    summary = env.run()

    assert (summary.published, summary.failed) == (1, 1)


def test_summary_is_written_to_journal_and_returned(make_env):
    env = make_env()

    summary = env.run()

    env.journal.info.assert_called_once()
    message, thing_uuid = env.journal.info.call_args.args
    assert thing_uuid == "THING"
    assert "2 file(s) sent" in message
    assert "0 skipped" in message and "0 failed" in message
    assert summary.published == 2


def test_nothing_to_reparse_still_writes_summary(make_env):
    env = make_env({})

    summary = env.run()

    assert (summary.published, summary.skipped, summary.failed) == (0, 0, 0)
    env.journal.info.assert_called_once()
    assert "0 file(s) sent" in env.journal.info.call_args.args[0]


class TestGetParseInfo:
    def test_successful_file_returns_parser_from_tag(self):
        minio = MagicMock()
        minio.get_object_tags.return_value = tags("successful", "P1")

        assert get_parse_info(minio, "b", "f") == (True, "P1")

    @pytest.mark.parametrize("status", ["failed", "db_insert_failed"])
    def test_failed_file_counts_as_unparsed(self, status):
        minio = MagicMock()
        minio.get_object_tags.return_value = tags(status, "P1")

        assert get_parse_info(minio, "b", "f") == (False, None)

    @pytest.mark.parametrize("value", [None, {}])
    def test_file_without_tags_counts_as_unparsed(self, value):
        minio = MagicMock()
        minio.get_object_tags.return_value = value

        assert get_parse_info(minio, "b", "f") == (False, None)

    def test_s3_error_counts_as_unparsed(self):
        minio = MagicMock()
        minio.get_object_tags.side_effect = S3Error(
            "NoSuchKey", "missing", "res", "rid", "hid", MagicMock()
        )

        assert get_parse_info(minio, "b", "f") == (False, None)


class TestToUtc:
    @pytest.mark.parametrize("value", [None, ""])
    def test_empty_value_is_none(self, value):
        assert _to_utc(value) is None

    def test_naive_value_gets_utc(self):
        assert _to_utc("2026-03-02 12:30:00") == datetime(
            2026, 3, 2, 12, 30, tzinfo=UTC
        )

    def test_aware_value_keeps_its_timezone(self):
        result = _to_utc("2026-03-02T12:30:00+02:00")

        assert result.utcoffset().total_seconds() == 2 * 3600
        assert result == datetime(2026, 3, 2, 10, 30, tzinfo=UTC)
