#! /usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd

from timeio.parser import CsvParser

RAWDATA = """
//Hydroinnova CRS-1000 Data
//CellSig=12

//RecordNum,Date Time(UTC),P1_mb,P3_mb,P4_mb,T1_C,T2_C,T3_C,T4_C,T_CS215,RH1,RH2,RH_CS215,Vbat,N1Cts,N2Cts,N1ET_sec,N2ET_sec,N1T_C,N1RH,N2T_C,N2RH,D1,

1418, 2021/09/09 05:45:00,  987.0, 989.70, 991.05,   15.9, 128.9,  15.8,  14.6,  13.8, 75.2,119.0, 89.2, 11.853,      160,      122,     900,     900,  17.9, 62.7,  17.7, 63.5,        0
1419, 2021/09/09 06:00:00,  987.0, 989.74, 991.05,   15.9, 128.9,  15.7,  14.5,  14.2, 75.6,119.0, 88.8, 11.856,      171,      111,     900,     900,  18.0, 62.9,  17.8, 63.6,        0
1420, 2021/09/09 06:15:00,  987.1, 989.76, 991.12,   15.9, 128.9,  15.8,  14.6,  14.5, 76.1,119.0, 89.5, 11.855,      165,      103,     900,     900,  18.1, 63.2,  17.9, 63.8,        0
"""

DIRTYDATA = """
//Hydroinnova CRS-1000 Data
//CellSig=12

//RecordNum,Date Time(UTC),P1_mb,P3_mb,P4_mb,T1_C,

1418, 2021/09/09 05:45:00,  987.0, 989.70, 991.05,   15.9
1419, 2021/09/09 06:00:00,  987.0,    xW8, 991.05,   15.9
1420, 2021/09/09 06:15:00,  987.1, 989.76, 991.12,   15.9
"""


def test_parsing():
    settings = {
        "decimal": ".",
        "delimiter": ",",
        "skiprows": 3,
        "skipfooter": 0,
        "index_col": 1,
        "date_format": "%Y/%m/%d %H:%M:%S",
    }
    parser = CsvParser(settings)
    df = parser.do_parse(RAWDATA)
    assert (df[3] == [989.7, 989.74, 989.76]).all()
    assert (df[15] == [122, 111, 103]).all()
    assert (df.columns == [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]).all()  # fmt: skip


def test_dirty_data_parsing():
    settings = {
        "decimal": ".",
        "delimiter": ",",
        "skiprows": 3,
        "skipfooter": 0,
        "index_col": 1,
        "date_format": "%Y/%m/%d %H:%M:%S",
    }

    parser = CsvParser(settings)
    df = parser.do_parse(DIRTYDATA)

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
