import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from access_scope import AccessScope
from constants import REPARSABLE_INGEST_TYPES
from models import TriggerReparseBase
from mqtt import mqtt_client
from mqtt.generate_mqtt_messages import create_reparse_files_msg
from routers import trigger_reparse as trigger_reparse_router
from services import trigger_reparse as trigger_reparse_service_module

SUPERUSER = AccessScope([], is_superuser=True)
NORMAL_USER = AccessScope([1, 2])


class TestCanReparse:
    def test_superuser_may_reparse(self):
        assert SUPERUSER.can_reparse(permission_group_id=99) is True

    def test_normal_user_may_not_reparse_even_in_own_group(self):
        assert NORMAL_USER.can_reparse(permission_group_id=1) is False


class TestReparsableIngestTypes:
    def test_only_file_based_ingests_are_reparsable(self):
        assert {str(t) for t in REPARSABLE_INGEST_TYPES} == {
            "sftp",
            "external_sftp",
            "http",
        }

    @pytest.mark.parametrize("ingest_type", ["sftp", "external_sftp", "http"])
    def test_plain_string_type_is_recognised(self, ingest_type):
        assert ingest_type in REPARSABLE_INGEST_TYPES

    @pytest.mark.parametrize(
        "ingest_type", ["mqtt", "external_api", "external_mqtt", "unknown"]
    )
    def test_other_types_are_not_reparsable(self, ingest_type):
        assert ingest_type not in REPARSABLE_INGEST_TYPES


class TestTriggerReparseModel:
    def test_defaults(self):
        payload = TriggerReparseBase(ingest_id=1)

        assert payload.start_date is None and payload.end_date is None
        assert payload.filename_pattern is None
        assert payload.parser_id is None
        assert payload.include_parsed is False
        assert payload.parsed_files_parser == "current"

    def test_accepts_all_fields(self):
        payload = TriggerReparseBase(
            ingest_id=1,
            start_date="2026-01-01",
            end_date="2026-01-02 12:00:00",
            filename_pattern="*.csv",
            parser_id=7,
            include_parsed=True,
            parsed_files_parser="original",
        )

        assert payload.parser_id == 7
        assert payload.parsed_files_parser == "original"

    def test_rejects_invalid_date_format(self):
        with pytest.raises(ValidationError):
            TriggerReparseBase(ingest_id=1, start_date="not-a-date")

    def test_rejects_end_before_start(self):
        with pytest.raises(ValidationError):
            TriggerReparseBase(
                ingest_id=1, start_date="2026-02-01", end_date="2026-01-01"
            )

    def test_rejects_unknown_parser_choice(self):
        with pytest.raises(ValidationError):
            TriggerReparseBase(ingest_id=1, parsed_files_parser="newest")

    def test_requires_ingest_id(self):
        with pytest.raises(ValidationError):
            TriggerReparseBase()

    def test_original_without_include_parsed_is_accepted(self):
        # documents the current decision: no validator rejects this combination
        payload = TriggerReparseBase(ingest_id=1, parsed_files_parser="original")

        assert payload.include_parsed is False


class TestReparseMessage:
    def test_contains_required_fields(self):
        ingest_uuid = uuid.uuid4()

        msg = create_reparse_files_msg(
            ingest_uuid, None, None, None, None, False, "current"
        )

        assert msg == {
            "version": 1,
            "thing": str(ingest_uuid),
            "include_parsed": False,
            "parsed_files_parser": "current",
        }

    def test_contains_optional_fields_when_given(self):
        msg = create_reparse_files_msg(
            "T", "2026-01-01", "2026-02-01", "*.csv", "P", True, "original"
        )

        assert msg["start_date"] == "2026-01-01"
        assert msg["end_date"] == "2026-02-01"
        assert msg["filename_pattern"] == "*.csv"
        assert msg["parser_uuid"] == "P"
        assert msg["include_parsed"] is True
        assert msg["parsed_files_parser"] == "original"

    def test_message_is_json_serialisable(self):
        import json

        msg = create_reparse_files_msg(
            uuid.uuid4(), "2026-01-01", None, None, None, False, "current"
        )

        json.dumps(msg)


class TestPublishTriggerReparse:
    def test_publishes_message_on_default_topic(self, monkeypatch):
        publish_message = MagicMock()
        monkeypatch.setattr(mqtt_client, "publish_message", publish_message)

        mqtt_client.publish_trigger_reparse(
            "ingest-uuid", None, None, None, None, False, "current"
        )

        msg, topic, _log = publish_message.call_args.args
        assert topic == "reparse_files_triggered"
        assert msg["thing"] == "ingest-uuid"

    def test_topic_can_be_overridden(self, monkeypatch):
        publish_message = MagicMock()
        monkeypatch.setattr(mqtt_client, "publish_message", publish_message)

        mqtt_client.publish_trigger_reparse(
            "u", None, None, None, None, False, "current", topic="other"
        )

        assert publish_message.call_args.args[1] == "other"


@pytest.fixture
def publish(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(trigger_reparse_service_module, "publish_trigger_reparse", mock)
    return mock


def make_ingest(ingest_type="sftp", permission_group_id=1):
    return SimpleNamespace(
        uuid="ingest-uuid",
        ingest_type=ingest_type,
        permission_group_id=permission_group_id,
    )


def run_service(payload, access_scope=SUPERUSER, ingest=None, repo_parser=None):
    repo_ingest = MagicMock()
    repo_ingest.find_one.return_value = ingest or make_ingest()
    repo_parser = repo_parser or MagicMock()
    result = trigger_reparse_service_module.trigger_reparse_service(
        payload=payload,
        repo_ingest=repo_ingest,
        repo_parser=repo_parser,
        access_scope=access_scope,
    )
    return result, repo_ingest, repo_parser


class TestTriggerReparseService:
    def test_superuser_triggers_reparse_with_all_options(self, publish):
        payload = TriggerReparseBase(
            ingest_id=5,
            start_date="2026-01-01",
            end_date="2026-02-01",
            filename_pattern="*.csv",
            include_parsed=True,
            parsed_files_parser="original",
        )

        result, repo_ingest, _ = run_service(payload)

        assert result == {"triggered_ingest": 5}
        repo_ingest.find_one.assert_called_once_with(5, access_scope=SUPERUSER)
        publish.assert_called_once_with(
            ingest_uuid="ingest-uuid",
            start_date="2026-01-01",
            end_date="2026-02-01",
            filename_pattern="*.csv",
            parser_uuid=None,
            include_parsed=True,
            parsed_files_parser="original",
        )

    def test_parser_id_is_resolved_to_parser_uuid(self, publish):
        parser_uuid = uuid.uuid4()
        repo_parser = MagicMock()
        repo_parser.find_one.return_value = SimpleNamespace(
            parser=SimpleNamespace(uuid=parser_uuid)
        )

        run_service(
            TriggerReparseBase(ingest_id=1, parser_id=7), repo_parser=repo_parser
        )

        repo_parser.find_one.assert_called_once_with(7, access_scope=SUPERUSER)
        assert publish.call_args.kwargs["parser_uuid"] == str(parser_uuid)

    def test_parser_is_not_looked_up_without_parser_id(self, publish):
        _, _, repo_parser = run_service(TriggerReparseBase(ingest_id=1))

        repo_parser.find_one.assert_not_called()

    def test_user_without_reparse_right_gets_403(self, publish):
        with pytest.raises(HTTPException) as exc_info:
            run_service(TriggerReparseBase(ingest_id=1), access_scope=NORMAL_USER)

        assert exc_info.value.status_code == 403
        publish.assert_not_called()

    def test_permission_is_checked_with_the_ingests_permission_group(self, publish):
        scope = MagicMock(spec=AccessScope)
        scope.can_reparse.return_value = True

        run_service(
            TriggerReparseBase(ingest_id=1),
            access_scope=scope,
            ingest=make_ingest(permission_group_id=42),
        )

        scope.can_reparse.assert_called_once_with(42)

    def test_forbidden_user_does_not_trigger_parser_lookup(self, publish):
        repo_parser = MagicMock()

        with pytest.raises(HTTPException):
            run_service(
                TriggerReparseBase(ingest_id=1, parser_id=7),
                access_scope=NORMAL_USER,
                repo_parser=repo_parser,
            )

        repo_parser.find_one.assert_not_called()

    @pytest.mark.parametrize("ingest_type", ["sftp", "external_sftp", "http"])
    def test_file_based_ingest_types_are_accepted(self, publish, ingest_type):
        run_service(TriggerReparseBase(ingest_id=1), ingest=make_ingest(ingest_type))

        publish.assert_called_once()

    @pytest.mark.parametrize("ingest_type", ["mqtt", "external_api", "external_mqtt"])
    def test_other_ingest_types_get_422(self, publish, ingest_type):
        with pytest.raises(HTTPException) as exc_info:
            run_service(
                TriggerReparseBase(ingest_id=1), ingest=make_ingest(ingest_type)
            )

        assert exc_info.value.status_code == 422
        publish.assert_not_called()

    def test_unknown_ingest_is_not_found(self, publish):
        repo_ingest = MagicMock()
        repo_ingest.find_one.side_effect = HTTPException(404, "Not found")

        with pytest.raises(HTTPException) as exc_info:
            trigger_reparse_service_module.trigger_reparse_service(
                payload=TriggerReparseBase(ingest_id=1),
                repo_ingest=repo_ingest,
                repo_parser=MagicMock(),
                access_scope=SUPERUSER,
            )

        assert exc_info.value.status_code == 404
        publish.assert_not_called()

    def test_unknown_parser_is_not_found(self, publish):
        repo_parser = MagicMock()
        repo_parser.find_one.side_effect = HTTPException(404, "Not found")

        with pytest.raises(HTTPException) as exc_info:
            run_service(
                TriggerReparseBase(ingest_id=1, parser_id=7), repo_parser=repo_parser
            )

        assert exc_info.value.status_code == 404
        publish.assert_not_called()


class TestTriggerReparseRouter:
    def test_router_passes_access_scope_of_current_user(self, monkeypatch):
        user = SimpleNamespace(id=1, permission_group_ids=[3], is_superuser=True)
        payload = TriggerReparseBase(ingest_id=1)
        repo_ingest, repo_parser = MagicMock(), MagicMock()
        service = MagicMock(return_value={"triggered_ingest": 1})
        monkeypatch.setattr(trigger_reparse_router, "trigger_reparse_service", service)

        result = trigger_reparse_router.trigger_reparse(
            current_user=user,
            payload=payload,
            repo_ingest=repo_ingest,
            repo_parser=repo_parser,
        )

        assert result == {"triggered_ingest": 1}
        kwargs = service.call_args.kwargs
        assert kwargs["payload"] is payload
        assert kwargs["repo_ingest"] is repo_ingest
        assert kwargs["repo_parser"] is repo_parser
        assert kwargs["access_scope"] == AccessScope([3], is_superuser=True)

    def test_router_is_registered_in_the_app(self):
        from main import app

        paths = {route.path for route in app.routes}

        assert "/trigger/reparse/" in paths
