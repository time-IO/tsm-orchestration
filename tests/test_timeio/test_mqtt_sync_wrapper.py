#! /usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from mqtt_sync_wrapper import get_bosch_timerange, TIMERANGE_MAPPING


def _mock_thing(settings):
    thing = MagicMock()
    thing.ext_api.settings = settings
    return thing


def test_get_bosch_timerange_with_bosch_settings():
    thing = _mock_thing({"period_in_minutes": 60})
    from_str, to_str = get_bosch_timerange(thing)

    from_dt = datetime.strptime(from_str, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    to_dt = datetime.strptime(to_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    delta_minutes = (to_dt - from_dt).total_seconds() / 60
    assert delta_minutes == pytest.approx(60, abs=1)


def test_get_bosch_timerange_with_sensoto_settings():
    """Regression test: sensoto previously had no `period_in_minutes` in its
    settings, causing get_bosch_timerange to raise a KeyError when used via
    TIMERANGE_MAPPING['sensoto']."""
    thing = _mock_thing({"network": "net1", "device": "dev1", "period_in_minutes": 15})
    from_str, to_str = get_bosch_timerange(thing)

    from_dt = datetime.strptime(from_str, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    to_dt = datetime.strptime(to_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    delta_minutes = (to_dt - from_dt).total_seconds() / 60
    assert delta_minutes == pytest.approx(15, abs=1)


def test_get_bosch_timerange_missing_period_raises_keyerror():
    """Documents the old bug: without period_in_minutes, get_bosch_timerange
    fails. Guards against silently reintroducing the bug for any api_type
    still mapped to get_bosch_timerange without that setting."""
    thing = _mock_thing({"network": "net1", "device": "dev1"})
    with pytest.raises(KeyError):
        get_bosch_timerange(thing)


def test_sensoto_mapped_to_bosch_timerange():
    assert TIMERANGE_MAPPING["sensoto"] is get_bosch_timerange
