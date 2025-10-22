#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import timeio.grafana.utils as grafana_utils
from unittest.mock import MagicMock
from timeio.grafana.dashboard import GrafanaDashboard
from grafana_client.client import GrafanaException
from timeio.grafana.user import GrafanaUser


@pytest.fixture
def mock_grafana_api():
    api = MagicMock()
    api.dashboard.get_dashboard.return_value = {
        "dashboard": {"uid": "thing_uuid", "title": "dashboar_title"}
    }
    api.dashboard.update_dashboard.return_value = None
    return api


@pytest.fixture
def mock_grafana_dashboard(mock_grafana_api):
    return GrafanaDashboard(api=mock_grafana_api)


@pytest.fixture
def mock_grafana_user(mock_grafana_api):
    return GrafanaUser(api=mock_grafana_api)


def test_exists_returns_true():
    func = MagicMock()
    result = grafana_utils._exists(func, 1, 2, 3)
    func.assert_called_once_with(1, 2, 3)
    assert result is True


def test_exists_returns_false():
    def raise_exception(*args):
        raise GrafanaException(response=None, message="msg", status_code=404)

    result = grafana_utils._exists(raise_exception, "abc")
    assert result is False


def test_dashboard_exists_true(mock_grafana_dashboard, mock_grafana_api):
    mock_grafana_api.dashboard.get_dashboard.return_value = {
        "dashboard": {"uid": "123"}
    }
    assert mock_grafana_dashboard._exists("123") is True


def test_dashboard_exists_false(mock_grafana_dashboard, mock_grafana_api):
    mock_grafana_api.dashboard.get_dashboard.side_effect = GrafanaException(
        response=None, message="msg", status_code=404
    )
    assert mock_grafana_dashboard._exists("123") is False


def test_user_get_id_true(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.users.find_user.return_value = {"id": 1}
    result = mock_grafana_user.get_id("user")
    assert result == 1
    mock_grafana_api.users.find_user.assert_called_once_with("user")


def test_user_get_id_false(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.users.find_user.side_effect = GrafanaException(
        response=None, message="msg", status_code=404
    )
    result = mock_grafana_user.get_id("user", max_tries=2, sleep=0)
    assert result is None
    assert mock_grafana_api.users.find_user.call_count == 2


def test_user_get_orgs(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.users.get_user_organisations.return_value = [
        {"name": "org_1", "role": "admin"},
        {"name": "org_2", "role": "viewer"},
    ]
    result = mock_grafana_user.get_orgs(1)
    assert result == {"org_1": "admin", "org_2": "viewer"}


def test_user_add_to_org(mock_grafana_api, mock_grafana_user):
    mock_grafana_user.add_to_org("admin", "user")
    mock_grafana_api.organization.add_user_current_organization.assert_called_once_with(
        {"role": "admin", "loginOrEmail": "user"}
    )


def test_user_is_in_team_true(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.users.get_user_teams.return_value = [{"id": 1}, {"id": 2}]
    assert mock_grafana_user.is_in_team(2, 100) is True


def test_user_is_in_team_false(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.users.get_user_teams.return_value = [{"id": 1}]
    assert mock_grafana_user.is_in_team(3, 100) is False


def test_user_add_to_team_new(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.t.team.get_id_by_name.return_value = 10
    mock_grafana_user.is_in_team = MagicMock(return_value=False)
    mock_grafana_user.add_to_team("org_1", 1)
    mock_grafana_api.teams.add_team_member.assert_called_once_with(10, 1)


def test_user_add_to_team_exists(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.t.team.get_id_by_name.return_value = 10
    mock_grafana_user.is_in_team = MagicMock(return_value=True)
    mock_grafana_user.add_to_team("org_1", 1)
    mock_grafana_api.teams.add_team_member.assert_not_called()


def test_user_remove_from_team_true(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.t.team.get_id_by_name.return_value = 10
    mock_grafana_user.is_in_team = MagicMock(return_value=True)
    mock_grafana_user.remove_from_team("org_1", 1)
    mock_grafana_api.teams.remove_team_member.assert_called_once_with(10, 1)


def test_user_remove_from_team_false(mock_grafana_api, mock_grafana_user):
    mock_grafana_api.t.team.get_id_by_name.return_value = 10
    mock_grafana_user.is_in_team = MagicMock(return_value=False)
    mock_grafana_user.remove_from_team("org_1", 1)
    mock_grafana_api.teams.remove_team_member.assert_not_called()


def test_user_update_orgs(mock_grafana_api, mock_grafana_user):
    mock_grafana_user.get_orgs = MagicMock(return_value={"org_1": "admin"})
    mock_grafana_api.t.org.get_names_and_ids.return_value = {"org_1": 1, "org_2": 2}
    mock_grafana_user.is_in_team = MagicMock(return_value=False)
    mock_grafana_user.add_to_org = MagicMock()
    mock_grafana_user.remove_from_org = MagicMock()
    mock_grafana_user.add_to_team = MagicMock()

    new_orgs = {"org_2": "member"}
    mock_grafana_user.update_orgs(10, "user", new_orgs)

    mock_grafana_user.add_to_org.assert_called_once_with("member", "user")
    mock_grafana_user.remove_from_org.assert_called_once_with(10)
    mock_grafana_user.add_to_team.assert_called_once_with("org_2", 10)
