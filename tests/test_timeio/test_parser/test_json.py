#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd
import pytest

from timeio.parser.json_parser import JsonParser

from timeio.errors import ParsingError

RAWDATA = """
{
"Datetime": "2025-08-12T13:01:23", // Messzeitpunkt (UTC, ISO 8601)
"Frame_count": 123, // Nachrichten-Sequenznummer, 0..65535
"Voltage": 3.6, // Batteriespannung [V]
"Firmware_version_ANALOG": 0, // Firmware-Version, 0..15
"Air_temperature": 25.51, // Umgebungstemperatur [°C]
"Relative_humidity": 45.23, // rel. Luftfeuchtigkeit [%rH]
"Electrical_voltage_1": 317, // Analogspannung Eingang #1 [μV]
"Electrical_voltage_2": 20, // Analogspannung Eingang #2 [μV]
"Electrical_voltage_3": 0, // Analogspannung Eingang #3 [μV]
// fehlt, da im Beispiel inaktiv: "Electrical_voltage_4": 0, // Analogspannung Eingang #4 [μV]
"Analog_input_voltage_range_1": 1, // Spannungsbereich Eingang #1
"Analog_input_voltage_range_2": 2, // Spannungsbereich Eingang #2
"Analog_input_voltage_range_3": 3, // Spannungsbereich Eingang #3
"Analog_input_voltage_range_4": 0 // Spannungsbereich Eingang #4
}
"""


def test_parsing():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "comment": "//",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(RAWDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Frame_count",
        "Voltage",
        "Firmware_version_ANALOG",
        "Air_temperature",
        "Relative_humidity",
        "Electrical_voltage_1",
        "Electrical_voltage_2",
        "Electrical_voltage_3",
        "Analog_input_voltage_range_1",
        "Analog_input_voltage_range_2",
        "Analog_input_voltage_range_3",
        "Analog_input_voltage_range_4",
    ]
    assert df.index.equals(pd.to_datetime(["2025-08-12 13:01:23"]))
    assert df["Frame_count"].tolist() == [123]
    assert df["Analog_input_voltage_range_4"].tolist() == [0]


MULTIDATECOLUMDATA = """
{
"Date": "2025-08-09",
"Time": "06:15:00",
"Frame_count": 123, ? Nachrichten-Sequenznummer, 0..65535
"Voltage": 3.6, ? Batteriespannung [V]
"Firmware_version_RAIN": 0, ? Firmware-Version, 0..15
"Air_temperature": 25.51, ? Umgebungstemperatur [°C]
"Relative_humidity": 45.23, ? rel. Luftfeuchtigkeit [%rH]
"Electrical_pulse_count_1": 0, ? Impulszählerwert Eingang #1
"Electrical_pulse_count_2": 10, ? Impulszählerwert Eingang #2
"Electrical_pulse_count_3": 3, ? Impulszählerwert Eingang #3
? fehlt, da im Beispiel inaktiv: "Electrical_pulse_count_4": 0, ? Impulszählerwert Eingang #4
"Pulse_count_active_status_1": 1, ? Impulszähler Eingang #1 aktiv?
"Pulse_count_active_status_2": 1, ? Impulszähler Eingang #2 aktiv?
"Pulse_count_active_status_3": 1, ? Impulszähler Eingang #3 aktiv?
"Pulse_count_active_status_4": 0 ? Impulszähler Eingang #4 aktiv?
}
"""


def test_multi_date_column_parsing():
    settings = {
        "timestamp_keys": [
            {"key": "Date", "format": "%Y-%m-%d"},
            {"key": "Time", "format": "%H:%M:%S"},
        ],
        "comment": "?",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(MULTIDATECOLUMDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Frame_count",
        "Voltage",
        "Firmware_version_RAIN",
        "Air_temperature",
        "Relative_humidity",
        "Electrical_pulse_count_1",
        "Electrical_pulse_count_2",
        "Electrical_pulse_count_3",
        "Pulse_count_active_status_1",
        "Pulse_count_active_status_2",
        "Pulse_count_active_status_3",
        "Pulse_count_active_status_4",
    ]
    assert df.index.equals(pd.to_datetime(["2025-08-09 06:15:00"]))
    assert df["Frame_count"].tolist() == [123]
    assert df["Pulse_count_active_status_4"].tolist() == [0]


NESTEDDATA = """
{
"Timestamp": { # UTC, date and time in separate fields
    "Date": "20240701",
    "Time": "123456"
    },
"Parameters": { # Nested Objekt with sensor data
    "Frame_count": 123, # Nachrichten-Sequenznummer, 0..65535
    "Voltage": 3.6, # Batteriespannung [V]
    "Firmware_version_SOIL": 0, # Firmware-Version, 0..15
    "Air_temperature": 25.51, # Umgebungstemperatur [°C]
    "Relative_humidity": 45.23, # rel. Luftfeuchtigkeit [%rH]
    "Soil_temperature_1": 15.5, # Bodentemperatur Sensor #1 [°C]
    "Soil_temperature_2": 14.7, # Bodentemperatur Sensor #2 [°C]
    "Soil_temperature_3": 13.1, # Bodentemperatur Sensor #3 [°C]
    "Soil_moisture_1": 12.3, # vol. Bodenwassergehalt Sensor #1 [Vol%]
    "Soil_moisture_2": 17.5, # vol. Bodenwassergehalt Sensor #2 [Vol%]
    "Soil_moisture_3": 18.1, # vol. Bodenwassergehalt Sensor #3 [Vol%]
    "Soil_permittivity_1": 2.3, # Permittivity Sensor #1
    "Soil_permittivity_2": 3.1, # Permittivity Sensor #2
    "Soil_permittivity_3": 4.0 # Permittivity Sensor #3
    }
}
"""


def test_nested_json_parsing():
    settings = {
        "timestamp_keys": [
            {"key": "Timestamp.Date", "format": "%Y%m%d"},
            {"key": "Timestamp.Time", "format": "%H%M%S"},
        ],
        "comment": "#",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(NESTEDDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Parameters.Frame_count",
        "Parameters.Voltage",
        "Parameters.Firmware_version_SOIL",
        "Parameters.Air_temperature",
        "Parameters.Relative_humidity",
        "Parameters.Soil_temperature_1",
        "Parameters.Soil_temperature_2",
        "Parameters.Soil_temperature_3",
        "Parameters.Soil_moisture_1",
        "Parameters.Soil_moisture_2",
        "Parameters.Soil_moisture_3",
        "Parameters.Soil_permittivity_1",
        "Parameters.Soil_permittivity_2",
        "Parameters.Soil_permittivity_3",
    ]
    assert df.index.equals(pd.to_datetime(["2024-07-01 12:34:56"]))
    assert df["Parameters.Frame_count"].tolist() == [123]
    assert df["Parameters.Soil_permittivity_3"].tolist() == [4.0]


# Note: the array data must be an array of objects (not an object with an array property)
# see also https://pandas.pydata.org/docs/reference/api/pandas.json_normalize.html
ARRAYDATA = """
[
    {
        "Datetime": "2025-01-01T00:00:00",
        "Frame_count": 123,
        "Voltage": 3.6,
        "Firmware_version_THL": 0,
        "Air_temperature": 25.51,
        "Relative_humidity": 45.23,
        "Illuminance": 123
    },
    {
        "Datetime": "2025-01-01T01:00:00",
        "Frame_count": 124,
        "Voltage": 3.55,
        "Firmware_version_THL": 0,
        "Air_temperature": 25.45,
        "Relative_humidity": 45.31,
        "Illuminance": 130
    },
    {
        "Datetime": "2025-01-01T02:00:00",
        "Frame_count": 125,
        "Voltage": 3.5,
        "Firmware_version_THL": 0,
        "Air_temperature": 25.37,
        "Relative_humidity": 45.27,
        "Illuminance": 128
    }
]
"""


def test_array_json_parsing():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
    }
    parser = JsonParser(settings)
    df = parser.do_parse(ARRAYDATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Frame_count",
        "Voltage",
        "Firmware_version_THL",
        "Air_temperature",
        "Relative_humidity",
        "Illuminance",
    ]
    assert df.index.equals(
        pd.to_datetime(
            ["2025-01-01 00:00:00", "2025-01-01 01:00:00", "2025-01-01 02:00:00"]
        )
    )
    assert df["Frame_count"].tolist() == [123, 124, 125]
    assert df["Illuminance"].tolist() == [123, 130, 128]


UNIX_S_DATA = """
[
    {
        "Datetime": 1782856800,
        "value": 1
    },
    {
        "Datetime": 1782943200,
        "value": 2
    },
    {
        "Datetime": 1783029600,
        "value": 3
    }
]
"""


def test_unix_seconds_timestamp():
    settings = {
        "timestamp_keys": [
            {"key": "Datetime", "format": "UNIX_S"},
        ]
    }

    parser = JsonParser(settings)
    df = parser.do_parse(UNIX_S_DATA, "thing", "project")

    expected_index = pd.DatetimeIndex(
        [
            "2026-06-30 22:00:00+00:00",
            "2026-07-01 22:00:00+00:00",
            "2026-07-02 22:00:00+00:00",
        ],
        tz="UTC",
    )

    assert df.index.equals(expected_index)
    assert df["value"].tolist() == [1, 2, 3]


UNIX_MS_DATA = """
[
    {
        "Datetime": 1782856800000,
        "value": 1
    },
    {
        "Datetime": 1782943200000,
        "value": 2
    },
    {
        "Datetime": 1783029600000,
        "value": 3
    }
]
"""


def test_unix_milliseconds_timestamp():
    settings = {
        "timestamp_keys": [
            {"key": "Datetime", "format": "UNIX_MS"},
        ]
    }

    parser = JsonParser(settings)
    df = parser.do_parse(UNIX_MS_DATA, "thing", "project")

    expected_index = pd.DatetimeIndex(
        [
            "2026-06-30 22:00:00+00:00",
            "2026-07-01 22:00:00+00:00",
            "2026-07-02 22:00:00+00:00",
        ],
        tz="UTC",
    )

    assert df.index.equals(expected_index)
    assert df["value"].tolist() == [1, 2, 3]


LORAWAN_DATA = """
{
    "deduplicationId": "9947541e-2f10-40a9-9b6f-1e51085325b5",
    "time": "2026-08-18T11:15:56.166747+00:00",
    "deviceInfo": {
        "tenantId": "700c0206-97d8-475a-a65d-f5a3175298fb",
        "deviceName": "THL 0613 ID #083 MCU 25028710",
        "devEui": "477191d4be5a97a3"
    },
    "devAddr": "62cbe321",
    "data": "AATdABEY/wGAC9YJiBQ8AAAAMwM=",
    "object": {
        "Firmware_version_THL": 0,
        "Voltage": 3.03,
        "Frame_count": 1245,
        "Illuminance": 51,
        "Air_temperature": 24.4,
        "Relative_humidity": 51.8,
        "Datetime_valid": 0,
        "Datetime_timezone": "UTC",
        "Datetime": "2025-01-13T23:15:11"
    },
    "rxInfo": [
        {
            "gatewayId": "024a2763d8cc605e",
            "rssi": -99
        }
    ]
}
"""


def test_measurement_key_extracts_nested_object():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "measurement_key": "object",
        "timezone": "UTC",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(LORAWAN_DATA.strip(), "thing", "project")

    assert df.columns.tolist() == [
        "Firmware_version_THL",
        "Voltage",
        "Frame_count",
        "Illuminance",
        "Air_temperature",
        "Relative_humidity",
        "Datetime_valid",
        "Datetime_timezone",
    ]
    assert df["Voltage"].tolist() == [3.03]
    assert df["Frame_count"].tolist() == [1245]


def test_measurement_key_localizes_timezone():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "measurement_key": "object",
        "timezone": "UTC",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(LORAWAN_DATA.strip(), "thing", "project")

    expected_index = pd.DatetimeIndex(["2025-01-13 23:15:11"], tz="UTC")
    assert df.index.equals(expected_index)


def test_missing_measurement_key_raises_parsing_error():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "measurement_key": "does_not_exist",
        "timezone": "UTC",
    }
    parser = JsonParser(settings)

    with pytest.raises(ParsingError, match="Measurement key"):
        parser.do_parse(LORAWAN_DATA.strip(), "thing", "project")


def test_without_measurement_key_and_timezone_keeps_root_and_naive_index():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "comment": "//",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(RAWDATA.strip(), "thing", "project")

    # unchanged behavior: no timezone configured -> naive index
    assert df.index.tz is None
    assert df.index.equals(pd.to_datetime(["2025-08-12 13:01:23"]))


def test_excluded_keys_removes_keys_from_root():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "comment": "//",
        "excluded_keys": ["Illuminance"],
    }
    parser = JsonParser(settings)
    df = parser.do_parse(RAWDATA.strip(), "thing", "project")

    assert "Illuminance" not in df.columns


def test_excluded_keys_removes_keys_from_measurement_key_object():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "measurement_key": "object",
        "timezone": "UTC",
        "excluded_keys": ["Illuminance", "Datetime_valid"],
    }
    parser = JsonParser(settings)
    df = parser.do_parse(LORAWAN_DATA.strip(), "thing", "project")

    assert "Illuminance" not in df.columns
    assert "Datetime_valid" not in df.columns
    assert "Voltage" in df.columns


def test_excluded_keys_on_array_data():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "excluded_keys": ["Illuminance"],
    }
    parser = JsonParser(settings)
    df = parser.do_parse(ARRAYDATA.strip(), "thing", "project")

    assert "Illuminance" not in df.columns
    assert df["Frame_count"].tolist() == [123, 124, 125]


def test_without_excluded_keys_keeps_all_columns():
    settings = {
        "timestamp_keys": [{"key": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "comment": "//",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(RAWDATA.strip(), "thing", "project")

    assert "Frame_count" in df.columns


LINA13_SENSOR_DATA = """
{
    "proband-id": "SU-Q993A",
    "sensor-id": "7A9F503CD22866F5",
    "calib-no2": "-21.76",
    "calib-co": "4.18",
    "calib-o3": "-46.74",
    "data": [
        {"ts": 1658133580721, "values": {"accel_x": -0.337, "accel_y": 5.28, "accel_z": 8.588}},
        {"ts": 1658133579888, "values": {"accel_x": -0.437, "accel_y": 6.376, "accel_z": 7.402}},
        {"ts": 1658133579883, "values": {"ambient_light": 138.9}},
        {"ts": 1658133579373, "values": {"ambient_light": 118.8}},
        {"ts": 1658133579115, "values": {"ambient_light": 105.6}},
        {"ts": 1658133579042, "values": {"ambient_light": 90.9}},
        {"ts": 1658133578779, "values": {"accel_x": -0.277, "accel_y": 8.718, "accel_z": 4.329}},
        {"ts": 1658133578524, "values": {"ambient_light": 76.5}},
        {"ts": 1658133577717, "values": {"accel_x": 0.096, "accel_y": 7.743, "accel_z": 6.572}},
        {"ts": 1658133577616, "values": {"ambient_light": 95.3}}
    ]
}
"""


def test_lina13_measurement_key_with_unix_ms_timestamp_per_row():
    settings = {
        "measurement_key": "data",
        "timestamp_keys": [{"key": "ts", "format": "UNIX_MS"}],
        "timezone": "UTC",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(LINA13_SENSOR_DATA.strip(), "thing", "project")

    # root-level metadata (proband-id, sensor-id, calib-*) must be gone
    assert "proband-id" not in df.columns
    assert "sensor-id" not in df.columns
    assert "calib-no2" not in df.columns

    # nested "values" object flattened into separate columns
    assert "values.accel_x" in df.columns
    assert "values.ambient_light" in df.columns

    # each of the 10 rows keeps its own individual, millisecond-precise timestamp
    assert len(df) == 10
    assert df.index.tz is not None
    assert str(df.index.tz) == "UTC"
    assert df.index[0] == pd.Timestamp("2022-07-18 08:39:40.721", tz="UTC")
    assert df.index[-1] == pd.Timestamp("2022-07-18 08:39:37.616", tz="UTC")

    # spot-check values: accel rows keep their values, ambient_light rows are NaN there
    assert df["values.accel_x"].iloc[0] == -0.337
    assert pd.isna(df["values.accel_x"].iloc[2])
    assert df["values.ambient_light"].iloc[2] == 138.9
