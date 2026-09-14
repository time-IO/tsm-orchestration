#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.parse import urldefrag

import numpy as np
import pandas as pd
import pytest
import requests
import saqc

from timeio.qc.saqc import STAMPLATESchemeFinal


DIMENSION_URL = (
    "https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/blob/main/"
    "src/timeio/qc/saqc.py"
)


@pytest.mark.parametrize(
    "data,flag_range_kwargs,flagged_positions,expected_measurement",
    [
        pytest.param(
            [800, 900, 1000, 1250],
            {"min": 900, "max": 1200, "label": "range check"},
            [0, 3],
            {
                "jsonld.id": "qualityMeasurement_1",
                "value": 255.0,
                "metric": (
                    "https://rdm-software.pages.ufz.de/saqc/_api/"
                    "saqc.SaQC.html#saqc.SaQC.flagRange"
                ),
                "parameters": {"min": 900, "max": 1200},
                "dimension": DIMENSION_URL,
            },
            id="below-range",
        ),
        pytest.param(
            [10, 20, 30],
            {"max": 25},
            [2],
            {
                "jsonld.id": "qualityMeasurement_1",
                "value": 255.0,
                "metric": (
                    "https://rdm-software.pages.ufz.de/saqc/_api/"
                    "saqc.SaQC.html#saqc.SaQC.flagRange"
                ),
                "parameters": {"max": 25},
                "dimension": DIMENSION_URL,
            },
            id="above-max-only",
        ),
        pytest.param(
            [5, 10, 15],
            {"min": 7, "flag": 100.0},
            [0],
            {
                "jsonld.id": "qualityMeasurement_1",
                "value": 100.0,
                "metric": (
                    "https://rdm-software.pages.ufz.de/saqc/_api/"
                    "saqc.SaQC.html#saqc.SaQC.flagRange"
                ),
                "parameters": {"min": 7},
                "dimension": DIMENSION_URL,
            },
            id="custom-flag",
        ),
    ],
)
def test_saqc_scheme_writes_inline_quality_measurements(
    data, flag_range_kwargs, flagged_positions, expected_measurement
):
    qc = saqc.SaQC(
        data=saqc.DictOfSeries(
            {"T1S33": pd.Series(data, dtype=float)}
        ),
        scheme=STAMPLATESchemeFinal(),
    )
    qc = qc.flagRange(field="T1S33", **flag_range_kwargs)
    quality = qc.flags["T1S33"]

    for pos, value in enumerate(quality):
        result_quality = value["resultQuality"]
        measurements = result_quality["hasQualityMeasurements"]
        primary = result_quality["primaryQualityMeasurement"]
        expected = expected_measurement.copy()
        if pos not in flagged_positions:
            expected["value"] = "-inf"

        assert primary == measurements[-1]
        assert measurements == [expected]


def test_saqc_scheme_writes_multiple_history_entries_as_quality_measurements():
    index = pd.RangeIndex(3)
    history = saqc.core.History(index=index)
    history.append(
        pd.Series([np.nan, 255.0, np.nan], index=index),
        meta={
            "func": "flagRange",
            "kwargs": {
                "min": 0,
                "max": 100,
                "flag": 255.0,
                "field": "T1S33",
                "dfilter": saqc.FILTER_ALL,
            },
        },
    )
    history.append(
        pd.Series([np.nan, 100.0, np.nan], index=index),
        meta={
            "func": "flagUniLOF",
            "kwargs": {
                "n": 20,
                "thresh": 1.5,
                "flag": 100.0,
                "field": "T1S33",
                "dfilter": saqc.FILTER_ALL,
            },
        },
    )
    flags = saqc.Flags({"T1S33": history})

    quality = STAMPLATESchemeFinal().toExternal(flags)["T1S33"]

    result_quality = quality.iloc[1]["resultQuality"]
    measurements = result_quality["hasQualityMeasurements"]
    primary = result_quality["primaryQualityMeasurement"]
    dimension = DIMENSION_URL
    unflagged_measurements = [
        {**measurement, "value": "-inf"} for measurement in measurements
    ]

    assert quality.iloc[0]["resultQuality"]["hasQualityMeasurements"] == (
        unflagged_measurements
    )
    assert quality.iloc[2]["resultQuality"]["hasQualityMeasurements"] == (
        unflagged_measurements
    )

    assert measurements == [
        {
            "jsonld.id": "qualityMeasurement_1",
            "value": 255.0,
            "metric": (
                "https://rdm-software.pages.ufz.de/saqc/_api/"
                "saqc.SaQC.html#saqc.SaQC.flagRange"
            ),
            "parameters": {"min": 0, "max": 100},
            "dimension": dimension,
        },
        {
            "jsonld.id": "qualityMeasurement_2",
            "value": 100.0,
            "metric": (
                "https://rdm-software.pages.ufz.de/saqc/_api/"
                "saqc.SaQC.html#saqc.SaQC.flagUniLOF"
            ),
            "parameters": {"n": 20, "thresh": 1.5},
            "dimension": dimension,
        },
    ]
    assert primary == measurements[-1]
    assert primary["metric"] == (
        "https://rdm-software.pages.ufz.de/saqc/_api/"
        "saqc.SaQC.html#saqc.SaQC.flagUniLOF"
    )
    assert {measurement["dimension"] for measurement in measurements} == {dimension}


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            f"{STAMPLATESchemeFinal.SAQC_DOCS_URL}#saqc.SaQC.flagRange",
            id="metric-flag-range",
        ),
        pytest.param(
            f"{STAMPLATESchemeFinal.SAQC_DOCS_URL}#saqc.SaQC.flagUniLOF",
            id="metric-flag-unilof",
        ),
        pytest.param(STAMPLATESchemeFinal.SAQC_DIMENSION_URL, id="dimension"),
    ],
)
def test_saqc_scheme_links_are_available(url):
    base_url, fragment = urldefrag(url)
    response = requests.get(base_url, timeout=10)

    assert response.status_code == 200
    if fragment:
        assert f'id="{fragment}"' in response.text or f"#{fragment}" in response.text
