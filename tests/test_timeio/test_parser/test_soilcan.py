from pathlib import Path

import pytest
import pandas as pd

from timeio.parser.soilcan_parser import SoilcanParser

DBD_FILE = Path(__file__).parent / "data" / "000_20230824T000020.DBD"


@pytest.mark.parametrize(
    "type,expected",
    [
        ("operating-parameters", [0.0, 0.0, 1.0, 24.0, 6.71]),
        ("sensor-data", [-72.9, -67.1, -413.0, 999.8, -123.5]),
        ("weighing-data", [11.2, 2956.3, 28.6, 3059.8, 0.8]),
    ],
)
def test_parse_soilcan_data(type, expected):
    rawdata = DBD_FILE.read_bytes()
    parser = SoilcanParser({"type": type, "header": False})
    df = parser.do_parse(rawdata, "project", "thing")
    assert df.iloc[0, :5].astype(float).to_list() == expected


@pytest.mark.parametrize(
    "type,expected",
    [
        (
            "operating-parameters",
            ["WasserUnten (State)", "WasserOben (State)", "Spg-12V (State)"],
        ),
        (
            "sensor-data",
            ["L_1_TS1_M_030 (hPa)", "L_1_TS1_M_050 (hPa)", "L_1_TS1_M_140 (hPa)"],
        ),
        (
            "weighing-data",
            ["L_1_WAG_D_000 (Kg)", "L_1_WAG_L_000 (Kg)", "L_2_WAG_D_000 (Kg)"],
        ),
    ],
)
def test_parse_soilcan_header(type, expected):
    rawdata = DBD_FILE.read_bytes()
    parser = SoilcanParser({"type": type, "header": True})
    df = parser.do_parse(rawdata, "project", "thing")
    assert df.columns[:3].to_list() == expected
