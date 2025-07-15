#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd
import pytest

from timeio.parser import CsvParser

RAWDATA = """
//Hydroinnova CRS-1000 Data
//CellSig=12

//RecordNum,Date Time(UTC),P1_mb,P3_mb,P4_mb,T1_C,T2_C,T3_C,T4_C,T_CS215,RH1,RH2,RH_CS215,Vbat,N1Cts,N2Cts,N1ET_sec,N2ET_sec,N1T_C,N1RH,N2T_C,N2RH,D1

1418, 2021/09/09 05:45:00,  987.0, 989.70, 991.05,   15.9, 128.9,  15.8,  14.6,  13.8, 75.2,119.0, 89.2, 11.853,      160,      122,     900,     900,  17.9, 62.7,  17.7, 63.5,        0
1419, 2021/09/09 06:00:00,  987.0, 989.74, 991.05,   15.9, 128.9,  15.7,  14.5,  14.2, 75.6,119.0, 88.8, 11.856,      171,      111,     900,     900,  18.0, 62.9,  17.8, 63.6,        0
1420, 2021/09/09 06:15:00,  987.1, 989.76, 991.12,   15.9, 128.9,  15.8,  14.6,  14.5, 76.1,119.0, 89.5, 11.855,      165,      103,     900,     900,  18.1, 63.2,  17.9, 63.8,        0
"""


@pytest.mark.parametrize(
    "settings, columns",
    [
        [{"skiprows": 3}, [2, 4, 8]],
        [{"skiprows": 3, "header": 3}, ["P1_mb", "P4_mb", "T4_C"]],
        [{"comment": "//", "header": 3}, ["P1_mb", "P4_mb", "T4_C"]],
    ],
)
def test_parsing(settings, columns):
    base_settings = {
        "decimal": ".",
        "delimiter": ",",
        "skipfooter": 0,
        "timestamp_columns": [{"column": 1, "format": "%Y/%m/%d %H:%M:%S"}],
    }
    parser = CsvParser({**base_settings, **settings})
    df = parser.do_parse(RAWDATA.strip(), "project", "thing")

    assert df.columns[[1, 3, 7]].equals(pd.Index(columns))
    assert (df.iloc[:, 2] == [989.7, 989.74, 989.76]).all()
    assert (df.iloc[:, 14] == [122, 111, 103]).all()

    tframe = df.iloc[:, 3].to_frame()
    obs = parser.to_observations(tframe, origin="test")

    assert set([d["datastream_pos"] for d in obs]) == set(map(str, tframe.columns))
    assert set([d["result_number"] for d in obs]) == set(tframe.squeeze().tolist())


DIRTYDATA = """
//Hydroinnova CRS-1000 Data
//CellSig=12

//RecordNum,Date Time(UTC),P1_mb,P3_mb,P4_mb,T1_C,

1418, 2021/09/09 05:45:00,  987.0, 989.70, 991.05,   15.9
1419, 2021/09/09 06:00:00,  987.0,    xW8, 991.05,   15.9
1420, 2021/09/09 06:15:00,  987.1, 989.76, 991.12,   15.9
"""


def test_dirty_data_parsing():
    settings = {
        "decimal": ".",
        "delimiter": ",",
        "skiprows": 3,
        "skipfooter": 0,
        "timestamp_columns": [{"column": 1, "format": "%Y/%m/%d %H:%M:%S"}],
    }

    parser = CsvParser(settings)
    df = parser.do_parse(DIRTYDATA, "project", "thing")

    assert pd.api.types.is_numeric_dtype(df[2])
    assert pd.api.types.is_string_dtype(df[3])

    obs = parser.to_observations(df[[3]], origin="test")
    assert len(obs) == 3
    assert obs[0] == {
        "result_time": "2021-09-09T06:00:00",
        "result_string": "xW8",
        "result_type": 1,
        "datastream_pos": "3",
        "parameters": '{"origin": "test", "column_header": "3"}',
    }

    assert obs[1] == {
        "result_time": "2021-09-09T05:45:00",
        "result_number": 989.7,
        "result_type": 0,
        "datastream_pos": "3",
        "parameters": '{"origin": "test", "column_header": "3"}',
    }


MULTIDATECOLUMDATA = """
============================================================================
   Datum     Zeit  Temp spezLeitf   Tiefe   Chl   Chl    ODO ODOsat Batterie
   t/m/j hh:mm:ss     C     uS/cm   Meter  ug/l   RFU   mg/l %Lokal     Volt
----------------------------------------------------------------------------
02/11/22 14:00:51 20.52         3   0.151   9.1   2.2   9.10  100.5     12.5
02/11/22 15:00:51 20.38         3   0.158 -23.5  -5.6   9.11  100.3     12.5
02/11/22 16:00:51 20.19         3   0.161  -0.5  -0.1   9.15  100.3     12.4
02/11/22 17:00:51 20.02         3   0.164   0.0   0.0   9.18  100.3     12.5
"""


def test_multi_date_column_parsing():
    settings = {
        "decimal": ".",
        "delimiter": "\\s+",
        "skiprows": 4,
        "skipfooter": 0,
        "header": None,
        "timestamp_columns": [
            {"column": 0, "format": "%d/%m/%y"},
            {"column": 1, "format": "%H:%M:%S"},
        ],
    }
    parser = CsvParser(settings)
    df = parser.do_parse(MULTIDATECOLUMDATA.strip(), "project", "thing")

    assert df.index.equals(
        pd.to_datetime(
            [
                "2022-11-02 14:00:51",
                "2022-11-02 15:00:51",
                "2022-11-02 16:00:51",
                "2022-11-02 17:00:51",
            ]
        )
    )
    assert df.columns.equals(pd.RangeIndex(2, 10))
    assert (df[2] == [20.52, 20.38, 20.19, 20.02]).all()
    assert (df[9] == [12.5, 12.5, 12.4, 12.5]).all()
