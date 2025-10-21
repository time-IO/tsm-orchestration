#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import timeio.grafana.utils as grafana_utils
from unittest.mock import MagicMock
from timeio.grafana.dashboard import GrafanaDashboard
from grafana_client.client import GrafanaException


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
