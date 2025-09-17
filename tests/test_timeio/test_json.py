#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd
import pytest

from test_csv import MULTIDATECOLUMDATA
from timeio.parser.json_parser import JsonParser
# from timeio.errors import ParsingError

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
        "timestamp_columns": [{"column": "Datetime", "format": "%Y-%m-%dT%H:%M:%S"}],
        "comment": "//",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(RAWDATA.strip())

    assert df.columns.tolist() == [
        'Frame_count', 'Voltage', 'Firmware_version_ANALOG', 'Air_temperature',
        'Relative_humidity', 'Electrical_voltage_1', 'Electrical_voltage_2',
        'Electrical_voltage_3', 'Analog_input_voltage_range_1',
        'Analog_input_voltage_range_2', 'Analog_input_voltage_range_3',
        'Analog_input_voltage_range_4'
    ]
    assert df.index.equals(pd.to_datetime(["2025-08-12 13:01:23"]))
    assert df["Frame_count"].tolist() == [123]
    assert df["Analog_input_voltage_range_4"].tolist() == [0]


MULTIDATECOLUMDATA="""    
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
        "timestamp_columns": [
            {"column": "Date", "format": "%Y-%m-%d"},
            {"column": "Time", "format": "%H:%M:%S"},
        ],
        "comment": "?",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(MULTIDATECOLUMDATA.strip())

    assert df.columns.tolist() == [
        'Frame_count', 'Voltage', 'Firmware_version_RAIN', 'Air_temperature',
        'Relative_humidity', 'Electrical_pulse_count_1',
        'Electrical_pulse_count_2', 'Electrical_pulse_count_3',
        'Pulse_count_active_status_1', 'Pulse_count_active_status_2',
        'Pulse_count_active_status_3', 'Pulse_count_active_status_4'
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
        "timestamp_columns": [
            {"column": "Timestamp.Date", "format": "%Y%m%d"},
            {"column": "Timestamp.Time", "format": "%H%M%S"},
        ],
        "comment": "#",
    }
    parser = JsonParser(settings)
    df = parser.do_parse(NESTEDDATA.strip())

    assert df.columns.tolist() == [
        'Parameters.Frame_count', 'Parameters.Voltage', 'Parameters.Firmware_version_SOIL',
        'Parameters.Air_temperature', 'Parameters.Relative_humidity', 'Parameters.Soil_temperature_1',
        'Parameters.Soil_temperature_2', 'Parameters.Soil_temperature_3', 'Parameters.Soil_moisture_1',
        'Parameters.Soil_moisture_2', 'Parameters.Soil_moisture_3', 'Parameters.Soil_permittivity_1',
        'Parameters.Soil_permittivity_2', 'Parameters.Soil_permittivity_3'
    ]
    assert df.index.equals(pd.to_datetime(["2024-07-01 12:34:56"]))
    assert df["Parameters.Frame_count"].tolist() == [123]
    assert df["Parameters.Soil_permittivity_3"].tolist() == [4.0]