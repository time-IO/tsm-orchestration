#! /usr/bin/env python

import pytest
from datetime import datetime
from timeio.parser.mqtt_devices.campbell_cr6 import CampbellCr6Parser
from timeio.parser.mqtt_devices.chirpstack_generic import ChirpStackGenericParser
from timeio.parser.mqtt_devices.ydoc_ml_417 import YdocMl417Parser
from timeio.errors import ParsingError
from timeio.parser import get_parser


def test_campbell_parser_basic():
    parser = CampbellCr6Parser()
    raw = {
        "properties": {
            "loggerID": "CR6_18341",
            "observationNames": ["Batt_volt_Min", "PTemp"],
            "observations": {"2022-05-24T08:53:00Z": [11.9, 26.91]},
        }
    }
    obs = parser.do_parse(raw, origin="device/topic")
    assert len(obs) == 2
    assert obs[0].header == "Batt_volt_Min"
    assert obs[1].header == "PTemp"


def test_chirpstack_parser_basic():
    parser = ChirpStackGenericParser()
    raw = {
        "time": "2025-01-01T00:00:00Z",
        "object": {"temp": 20, "humidity": 50, "Data_time": "ignore_me"},
    }
    obs = parser.do_parse(raw, origin="chirp/test")
    assert len(obs) == 2
    assert all(o.header in ["temp", "humidity"] for o in obs)


def test_ydoc_ml417_parser_only_data_jsn():
    parser = YdocMl417Parser()
    assert parser.do_parse({"data": []}, origin="something") == []


def test_ydoc_ml417_parser_valid():
    parser = YdocMl417Parser()
    raw = {
        "data": [
            {
                "$ts": 250101000000,
                "MINVi": 1.0,
                "AVGVi": 3,
                "AVGCi": 100,
                "P1*": "0*T",
                "P2": "0*T",
                "P3": "0*T",
                "P4": "0*T",
            }
        ]
    }
    obs = parser.do_parse(raw, origin="data/jsn")
    assert len(obs) == 7
    assert isinstance(obs[0].timestamp, datetime)


@pytest.mark.parametrize(
    "parser_type, raw, start, end",
    [
        (
            "campbell_cr6",
            {
                "properties": {
                    "loggerID": "CR6_18341",
                    "observationNames": ["Batt_volt_Min", "PTemp"],
                    "observations": {
                        "2022-05-24T08:54:00Z": [11.8, 26.95],
                        "2022-05-24T08:53:00Z": [11.9, 26.91],
                    },
                }
            },
            "2022-05-24T08:53:00+00:00",
            "2022-05-24T08:54:00+00:00",
        ),
        (
            "chirpstack_generic",
            {"time": "2025-01-01T00:00:00Z", "object": {"temp": 20}},
            "2025-01-01T00:00:00+00:00",
            "2025-01-01T00:00:00+00:00",
        ),
        (
            "ydoc_ml417",
            {
                "data": [
                    {
                        "$ts": 250101000000,
                        "MINVi": 1.0,
                        "AVGVi": 3,
                        "AVGCi": 100,
                        "P1*": "0*T",
                        "P2": "0*T",
                        "P3": "0*T",
                        "P4": "0*T",
                    },
                    {
                        "$ts": 250101001000,
                        "MINVi": 1.1,
                        "AVGVi": 3,
                        "AVGCi": 100,
                        "P1*": "0*T",
                        "P2": "0*T",
                        "P3": "0*T",
                        "P4": "0*T",
                    },
                ]
            },
            "2025-01-01T00:00:00",
            "2025-01-01T00:10:00",
        ),
        (
            "quaesta",
            {
                "stationID": "Site118",
                "loggerID": "QI-DL2200-SN-25100118",
                "type": "dataCRNS",
                "timestampISO8601": "2026-05-20T16:00:00Z",
                "timestampEpoch": 1779292800,
                "dataSelect": "p3t3h3n1e1s1w1w2",
                "recordNum": 4,
                "P1_mb": 929.2,
                "T1_degC": 26.6,
            },
            "2026-05-20T16:00:00+00:00",
            "2026-05-20T16:00:00+00:00",
        ),
    ],
)
def test_device_parsers_report_date_range(parser_type, raw, start, end):
    parser = get_parser(parser_type, None)
    origin = "mqtt_ingest/user/logger/data/jsn"
    observations = parser.to_observations(parser.do_parse(raw, origin), "thing-uuid")
    assert observations
    assert parser.start_date == start
    assert parser.end_date == end


@pytest.mark.parametrize(
    "parser_type, raw, match",
    [
        ("campbell_cr6", {"properties": {"observations": {}}}, "observationNames"),
        ("chirpstack_generic", {"object": {"temp": 1}}, "'time' and 'object'"),
        ("ydoc_ml417", {"foo": 1}, "'data'"),
        ("quaesta", {"type": "dataCRNS", "P1_mb": 1.0}, "timestampISO8601"),
        (
            "quaesta",
            {"type": "dataCRNS", "timestampISO8601": "yesterday"},
            "Invalid 'timestampISO8601'",
        ),
    ],
)
def test_device_parsers_raise_meaningful_error(parser_type, raw, match):
    parser = get_parser(parser_type, None)
    with pytest.raises(ParsingError, match=match):
        parser.do_parse(raw, "data/jsn")
