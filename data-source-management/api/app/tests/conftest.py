import pytest


@pytest.fixture
def sample_datastream_refs():
    return ["ds1", "ds2", "ds3"]


@pytest.fixture
def sample_qc_function_payload():
    return {
        "name": "flagIsolated",
        "quality_control_function_arguments": [
            {
                "name": "field",
                "type": "datastream",
                "input": {"value": ["temperature_sensor_1"]},
            },
            {"name": "gap_window", "type": "offset", "input": {"value": "2H"}},
            {"name": "group_window", "type": "offset", "input": {"value": "1D"}},
        ],
    }


@pytest.fixture
def sample_quality_control_function_argument_create():
    from models.quality_control_setting import QualityControlFunctionArgumentCreate

    return QualityControlFunctionArgumentCreate(
        name="field", type="datastream", input={"value": ["ds1"]}
    )


@pytest.fixture
def sample_quality_control_function_create():
    from models.quality_control_setting import (
        QualityControlFunctionArgumentCreate,
        QualityControlFunctionCreate,
    )

    return QualityControlFunctionCreate(
        name="flagIsolated",
        quality_control_function_arguments=[
            QualityControlFunctionArgumentCreate(
                name="field", type="datastream", input={"value": ["ds1"]}
            ),
            QualityControlFunctionArgumentCreate(
                name="gap_window", type="offset", input={"value": "2h"}
            ),
            QualityControlFunctionArgumentCreate(
                name="group_window", type="offset", input={"value": "1D"}
            ),
        ],
    )
