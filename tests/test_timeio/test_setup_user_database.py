#!/usr/bin/env python3

from unittest.mock import ANY, MagicMock

import pytest

import setup_user_database as sud
from setup_user_database import CreateThingInPostgresHandler


@pytest.fixture
def sql_dir(tmp_path, monkeypatch):
    (tmp_path / "views").mkdir()
    (tmp_path / "postgres-ddl.sql").write_text("CREATE TABLE thing (id int);")
    monkeypatch.setattr(sud, "SQL_DIR", tmp_path)
    monkeypatch.setattr(sud, "DDL_FILE", tmp_path / "postgres-ddl.sql")
    return tmp_path


def write(path, text):
    path.write_text(text)
    return path


def test_compute_views_version_stable(sql_dir):
    f = write(sql_dir / "views" / "a.sql", "CREATE VIEW a AS SELECT 1;")
    digest = sud.hash_view_files([f])
    assert sud.compute_views_version(digest, 1) == sud.compute_views_version(
        sud.hash_view_files([f]), 1
    )


def test_compute_views_version_changes(sql_dir, monkeypatch):
    f = write(sql_dir / "views" / "a.sql", "CREATE VIEW a AS SELECT 1;")
    monkeypatch.setenv("SMS_URL", "https://sms")
    monkeypatch.setenv("CV_URL", "https://cv")
    base = sud.compute_views_version(sud.hash_view_files([f]), 1)

    assert sud.compute_views_version(sud.hash_view_files([f]), 2) != base

    monkeypatch.setenv("SMS_URL", "https://other")
    assert sud.compute_views_version(sud.hash_view_files([f]), 1) != base
    monkeypatch.setenv("SMS_URL", "https://sms")

    monkeypatch.setenv("CV_URL", "https://other")
    assert sud.compute_views_version(sud.hash_view_files([f]), 1) != base
    monkeypatch.setenv("CV_URL", "https://cv")

    monkeypatch.setattr(sud, "VIEWS_REVISION", sud.VIEWS_REVISION + 1)
    assert sud.compute_views_version(sud.hash_view_files([f]), 1) != base


def test_hash_view_files_tracks_content_and_ddl(sql_dir):
    f = write(sql_dir / "views" / "a.sql", "CREATE VIEW a AS SELECT 1;")
    base = sud.hash_view_files([f])

    write(f, "CREATE VIEW a AS SELECT 2;")
    changed = sud.hash_view_files([f])
    assert changed != base

    write(sql_dir / "postgres-ddl.sql", "CREATE TABLE thing (id bigint);")
    assert sud.hash_view_files([f]) != changed


def test_view_files_exist():
    for kind, files in sud.VIEW_FILES.items():
        assert files, kind
        for f in files:
            assert f.is_file(), f


@pytest.fixture
def handler(monkeypatch):
    h = object.__new__(CreateThingInPostgresHandler)
    h.dsmdb_dsn = "dsn"
    h.views_digests = {"sta": "d-sta", "sti": "d-sti", "grf": "d-grf"}
    h.db = MagicMock()

    thing = MagicMock()
    thing.database.username = "User_1"
    thing.database.ro_username = "ro_user_1"
    monkeypatch.setattr(sud.Thing, "from_uuid", MagicMock(return_value=thing))
    monkeypatch.setattr(sud, "journal", MagicMock())

    for name in (
        "upsert_schema_thing_mapping",
        "upsert_thing",
        "deploy_view_files",
        "set_views_stamp",
        "grant_sta_select",
        "grant_grafana_select",
    ):
        setattr(h, name, MagicMock())
    h.user_exists = MagicMock(return_value=True)
    h.get_flyway_rank = MagicMock(return_value=7)
    h.views_up_to_date = MagicMock(return_value=True)
    return h


def run_act(h):
    h.act({"thing": "uuid"}, MagicMock())


def deployed(h):
    return [c.args[2:] for c in h.deploy_view_files.call_args_list]


def stamped(h):
    return [c.args[1:3] for c in h.set_views_stamp.call_args_list]


def test_act_skips_up_to_date_views_but_grants(handler):
    run_act(handler)

    handler.deploy_view_files.assert_not_called()
    handler.set_views_stamp.assert_not_called()
    assert handler.grant_sta_select.call_count == 2
    handler.grant_grafana_select.assert_called_once()


def test_act_checks_each_kind_in_its_schema(handler):
    run_act(handler)

    calls = [c.args for c in handler.views_up_to_date.call_args_list]
    assert [(s, k) for s, k, _ in calls] == [
        ("user_1", "sta"),
        ("user_1_int", "sti"),
        ("user_1", "grf"),
    ]
    expected = sud.compute_views_version("d-sti", 7)
    assert calls[1][2] == expected


def test_act_redeploys_only_stale_kind(handler):
    handler.views_up_to_date.side_effect = lambda schema, kind, version: kind != "sti"

    run_act(handler)

    assert deployed(handler) == [("sti", "user_1_int")]
    handler.set_views_stamp.assert_called_once_with(
        ANY, "user_1_int", "sti", sud.compute_views_version("d-sti", 7)
    )


def test_act_redeploys_all_when_stale(handler):
    handler.views_up_to_date.return_value = False

    run_act(handler)

    expected = [("sta", "user_1"), ("sti", "user_1_int"), ("grf", "user_1")]
    assert deployed(handler) == expected
    assert stamped(handler) == [(t, k) for k, t in expected]


def test_act_stamps_in_deploy_transaction(handler):
    handler.views_up_to_date.side_effect = lambda schema, kind, version: kind != "grf"

    run_act(handler)

    deploy_cursor = handler.deploy_view_files.call_args.args[0]
    assert handler.set_views_stamp.call_args.args[0] is deploy_cursor


def test_act_does_not_stamp_failed_deploy(handler):
    handler.views_up_to_date.return_value = False

    def deploy(c, thing, kind, target):
        if kind == "sti":
            raise RuntimeError("lock timeout")

    handler.deploy_view_files.side_effect = deploy

    with pytest.raises(RuntimeError):
        run_act(handler)

    assert stamped(handler) == [("user_1", "sta")]
    assert [k for k, _ in deployed(handler)] == ["sta", "sti"]


def test_deploy_view_files_substitutes_placeholders(sql_dir, monkeypatch):
    f = write(
        sql_dir / "views" / "a.sql",
        "SELECT '{tsm_schema}', '{target_schema}', '{sms_url}', '{cv_url}', '{}';",
    )
    monkeypatch.setitem(sud.VIEW_FILES, "sti", [f])
    monkeypatch.setenv("SMS_URL", "https://sms/o'brien")
    monkeypatch.setenv("CV_URL", "https://cv")
    h = object.__new__(CreateThingInPostgresHandler)
    thing = MagicMock()
    thing.database.schema = "User_1"
    c = MagicMock()

    h.deploy_view_files(c, thing, "sti", "user_1_int")

    executed = [call.args[0] for call in c.execute.call_args_list]
    assert executed[1] == "SET lock_timeout TO '30s'"
    assert executed[-1] == (
        "SELECT 'user_1', 'user_1_int', 'https://sms/o''brien', 'https://cv', '{}';"
    )


def test_deploy_view_files_ignores_unused_missing_env(sql_dir, monkeypatch):
    f = write(sql_dir / "views" / "g.sql", "CREATE VIEW g AS SELECT 1;")
    monkeypatch.setitem(sud.VIEW_FILES, "grf", [f])
    monkeypatch.delenv("SMS_URL", raising=False)
    monkeypatch.delenv("CV_URL", raising=False)
    h = object.__new__(CreateThingInPostgresHandler)
    c = MagicMock()

    h.deploy_view_files(c, MagicMock(), "grf", "user_1")

    executed = [call.args[0] for call in c.execute.call_args_list]
    assert executed[1] == "SET lock_timeout TO '10s'"
    assert executed[-1] == "CREATE VIEW g AS SELECT 1;"
