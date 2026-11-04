from pathlib import Path

import pandas as pd
import pytest

from timeio.errors import EmptyDataError, ParsingError
from timeio.parser import CsvParser, NutNetSoilParser, get_parser

SETTINGS = {
    "timezone": "Etc/GMT-1",
    "timestamp_columns": [{"column": 0, "format": "%d.%m.%Y %H:%M:%S"}],
}
TIMESTAMP = "13.09.2025 03:54:37"


def test_parsing_output():
    rawdata = (
        "13.09.2025 03:54:37,"
        "1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,"
        "11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,"
        "21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,"
        "31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,"
        "41.5,42.5,43.5,44.5,45.5,46.5,47.5,48.5,49.5,50.5,"
        "51.5,52.5,53.5,54.5,55.5,56.5,57.5,58.5,59.5,60.5\n"
        "\n"
        "13.09.2025 04:04:37,"
        "101.5,102.5,103.5,104.5,105.5,,,"
        "116.5,117.5,118.5,119.5,120.5,"
        "121.5,122.5,123.5,124.5,125.5,126.5,127.5,128.5,129.5,130.5,"
        "131.5,132.5,133.5,134.5,135.5,136.5,137.5,138.5,139.5,140.5,"
        "141.5,142.5,143.5,144.5,145.5,146.5,147.5,148.5,149.5,150.5,"
        "151.5,152.5,153.5,154.5,155.5,\n"
    )
    # Independently specify every expected value, without using CsvParser or
    # the cleanup helper to construct the expected frame. Sensors 2, 3 and 12
    # are missing in the second row (columns 6–15 and 56–60).
    expected = pd.DataFrame(
        [
            [column + 0.5 for column in range(1, 61)],
            [
                float("nan") if 6 <= column <= 15 or column >= 56 else column + 100.5
                for column in range(1, 61)
            ],
        ],
        columns=list(range(1, 61)),
        index=pd.DatetimeIndex(
            ["2025-09-13 03:54:37", "2025-09-13 04:04:37"], tz="Etc/GMT-1", name=0
        ),
    )

    actual = NutNetSoilParser().do_parse(rawdata, "project", "thing")

    pd.testing.assert_frame_equal(actual, expected, check_exact=True)


def test_fixed_settings_ignore_factory_parameters():
    parser = get_parser(
        "nutnet_soil", {"delimiter": ";", "header": 0, "timezone": "UTC"}
    )
    df = parser.do_parse(TIMESTAMP + ",1.25" * 60, "project", "thing")
    assert df.shape == (1, 60)
    assert (df.iloc[0] == 1.25).all()
    assert df.index[0] == pd.Timestamp("2025-09-13 03:54:37", tz="Etc/GMT-1")
    assert str(df.index.tz) == "Etc/GMT-1"


def test_constructor_accepts_no_user_settings():
    with pytest.raises(TypeError):
        NutNetSoilParser({"timezone": "UTC"})


def test_settings_are_independent():
    parser = NutNetSoilParser()
    parser.settings["timestamp_columns"][0]["format"] = "changed"
    assert (
        NutNetSoilParser().settings["timestamp_columns"]
        == SETTINGS["timestamp_columns"]
    )


@pytest.mark.parametrize(
    "missing", [{0}, {5}, {11}, {3, 4, 5}, {0, 5, 11}, {10, 11}, set(range(12))]
)
def test_missing_sensor_groups(missing):
    raw_fields = [TIMESTAMP]
    expected_fields = [TIMESTAMP]
    for group in range(12):
        values = [str(group * 5 + i) for i in range(1, 6)]
        raw_fields.extend([""] if group in missing else values)
        expected_fields.extend([""] * 5 if group in missing else values)
    rawdata = ",".join(raw_fields)
    expected = ",".join(expected_fields)

    assert NutNetSoilParser._cleanup(rawdata) == expected
    assert NutNetSoilParser._cleanup(expected) == expected
    parser = get_parser("nutnet_soil", None)
    actual = parser.do_parse(rawdata, "project", "thing")
    pd.testing.assert_frame_equal(
        actual, CsvParser(SETTINGS).do_parse(expected, "project", "thing")
    )
    assert parser.start_date == "2025-09-13T03:54:37+01:00"
    assert parser.end_date == parser.start_date


def test_blank_lines_and_complete_rows():
    complete = TIMESTAMP + ",1" * 60
    rawdata = f"\n\n \t\n{complete}\r\n\r\n{complete}  \n\n"
    assert NutNetSoilParser._cleanup(rawdata) == f"{complete}\n{complete}"


@pytest.mark.parametrize("rawdata", ["", "\n\n \t\n"])
def test_empty_data(rawdata):
    with pytest.raises(EmptyDataError):
        NutNetSoilParser().do_parse(rawdata, "project", "thing")


@pytest.mark.parametrize(
    "row",
    [
        TIMESTAMP + ",1" * 55,  # No missing-group marker.
        TIMESTAMP + ",1" * 51 + ",",  # Trailing group can only expand once.
        TIMESTAMP + ",1" * 57 + ",,",  # Four fields would overshoot the width.
    ],
)
def test_unrepairable_rows_raise(row):
    with pytest.raises(ParsingError, match="line 2: cannot repair row"):
        NutNetSoilParser().do_parse("\n" + row, "project", "thing")


def test_attached_sample():
    rawdata = (
        Path(__file__).parent / "fixtures" / "B7P4IF_example_columnshifts.txt"
    ).read_text()
    cleaned = NutNetSoilParser._cleanup(rawdata)
    assert len(cleaned.splitlines()) == 69
    assert all(line.count(",") == 60 for line in cleaned.splitlines())
    assert NutNetSoilParser._cleanup(cleaned) == cleaned

    parser = NutNetSoilParser()
    df = parser.do_parse(rawdata, "project", "thing")
    assert df.shape == (69, 60)
    assert list(df.columns) == list(range(1, 61))
    # The eighth row lost sensors 4–6; sensor 7 must remain in columns 31–35.
    row = df.loc[pd.Timestamp("2025-09-13 03:54:37", tz="Etc/GMT-1")]
    assert row.loc[16:30].isna().all()
    assert row.loc[31:35].tolist() == [12189, 13.23, 24.69, 17.438, 5.33]
    assert row[60] == 5.36
    assert parser.start_date == "2025-09-13T02:44:37+01:00"
    assert parser.end_date == "2025-09-13T14:04:37+01:00"


def test_fixed_timezone_in_winter_and_summer():
    rawdata = "\n".join(
        timestamp + ",1" * 60
        for timestamp in ("15.01.2025 12:00:00", "15.07.2025 12:00:00")
    )
    df = NutNetSoilParser().do_parse(rawdata, "project", "thing")
    assert [timestamp.isoformat() for timestamp in df.index] == [
        "2025-01-15T12:00:00+01:00",
        "2025-07-15T12:00:00+01:00",
    ]
    assert df.index.tz_convert("UTC").hour.tolist() == [11, 11]
