import json

import numpy as np
import pandas as pd
import pytest

from timeio.parser import CsvParser
from timeio.common import ObservationResultType
from timeio.errors import ParsingError


@pytest.fixture
def parser():
    return CsvParser()


@pytest.fixture
def index():
    return pd.DatetimeIndex(
        [
            "2025-01-01T12:00:00",
            "2025-01-01T12:01:00",
            "2025-01-01T12:02:00",
        ]
    )


def test_numeric_column(parser, index):
    data = pd.DataFrame(
        {
            "temperature": [1.0, 2.5, 3.0],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
        parser_uuid="parser-123",
    )

    assert len(observations) == 3

    assert observations[0]["result_time"] == "2025-01-01T12:00:00"
    assert observations[0]["result_number"] == 1.0
    assert observations[0]["result_type"] == ObservationResultType.Number
    assert observations[0]["datastream_pos"] == "temperature"

    assert observations[1]["result_number"] == 2.5
    assert observations[2]["result_number"] == 3.0


def test_string_column(parser, index):
    data = pd.DataFrame(
        {
            "status": ["ok", "warning", "error"],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert len(observations) == 3

    assert observations[0]["result_string"] == "ok"
    assert observations[0]["result_type"] == ObservationResultType.String
    assert observations[0]["datastream_pos"] == "status"

    assert observations[1]["result_string"] == "warning"
    assert observations[2]["result_string"] == "error"


def test_nan_values_are_omitted(parser, index):
    data = pd.DataFrame(
        {
            "temperature": [1.0, np.nan, 3.0],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert len(observations) == 2

    assert observations[0]["result_time"] == "2025-01-01T12:00:00"
    assert observations[0]["result_number"] == 1.0

    assert observations[1]["result_time"] == "2025-01-01T12:02:00"
    assert observations[1]["result_number"] == 3.0


def test_none_values_in_string_column_are_omitted(parser, index):
    data = pd.DataFrame(
        {
            "status": ["ok", None, "error"],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert len(observations) == 2

    assert observations[0]["result_string"] == "ok"
    assert observations[1]["result_string"] == "error"


def test_mixed_numeric_and_string_column_is_split(parser, index):
    data = pd.DataFrame(
        {
            "value": [1.5, "transmission error", 3.5],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert len(observations) == 3

    numeric = [
        observation for observation in observations if "result_number" in observation
    ]
    strings = [
        observation for observation in observations if "result_string" in observation
    ]

    assert len(numeric) == 2
    assert len(strings) == 1

    assert {
        observation["result_time"]: observation["result_number"]
        for observation in numeric
    } == {
        "2025-01-01T12:00:00": 1.5,
        "2025-01-01T12:02:00": 3.5,
    }

    assert strings[0]["result_time"] == "2025-01-01T12:01:00"
    assert strings[0]["result_string"] == "transmission error"
    assert strings[0]["result_type"] == ObservationResultType.String


def test_whitespace_is_stripped_from_strings_in_mixed_column(parser, index):
    data = pd.DataFrame(
        {
            "value": [1, "  transmission error  ", 3],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    string_observation = next(
        observation for observation in observations if "result_string" in observation
    )

    assert string_observation["result_string"] == "transmission error"


def test_whitespace_is_not_stripped_from_pure_string_column(parser, index):
    """
    Documents the current behaviour of the old implementation.

    Pure string columns are not stripped, while string values in mixed
    numeric/string columns are.
    """
    data = pd.DataFrame(
        {
            "value": ["  foo  ", "bar", "baz"],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert observations[0]["result_string"] == "  foo  "


def test_numeric_strings_are_converted_to_numbers(parser, index):
    data = pd.DataFrame(
        {
            "value": ["1.5", "2", "3.25"],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert len(observations) == 3

    assert all("result_number" in observation for observation in observations)

    assert [observation["result_number"] for observation in observations] == [
        1.5,
        2.0,
        3.25,
    ]


def test_mixed_numeric_strings_and_text(parser, index):
    data = pd.DataFrame(
        {
            "value": ["1.5", "error", "3.25"],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    numeric = {
        observation["result_time"]: observation["result_number"]
        for observation in observations
        if "result_number" in observation
    }

    strings = {
        observation["result_time"]: observation["result_string"]
        for observation in observations
        if "result_string" in observation
    }

    assert numeric == {
        "2025-01-01T12:00:00": 1.5,
        "2025-01-01T12:02:00": 3.25,
    }

    assert strings == {
        "2025-01-01T12:01:00": "error",
    }


def test_column_name_is_used_as_datastream_pos(parser, index):
    data = pd.DataFrame(
        {
            42: [1.0, 2.0, 3.0],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert all(observation["datastream_pos"] == "42" for observation in observations)


def test_parameters(parser, index):
    data = pd.DataFrame(
        {
            "temperature": [1.0, 2.0, 3.0],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
        parser_uuid="parser-123",
    )

    parameters = json.loads(observations[0]["parameters"])

    assert parameters["origin"] == "test.csv"
    assert parameters["column_header"] == "temperature"
    assert parameters["parser_id"] == "parser-123"
    assert "parsed_at" in parameters

    # Verify that parsed_at contains a valid ISO datetime.
    pd.Timestamp(parameters["parsed_at"])


def test_parser_uuid_may_be_none(parser, index):
    data = pd.DataFrame(
        {
            "temperature": [1.0],
        },
        index=index[:1],
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    parameters = json.loads(observations[0]["parameters"])

    assert parameters["parser_id"] is None


def test_input_dataframe_is_not_modified(parser, index):
    data = pd.DataFrame(
        {
            "temperature": [1.0, 2.0, 3.0],
        },
        index=index,
    )
    original = data.copy(deep=True)

    parser.to_observations(
        data,
        origin="test.csv",
    )

    pd.testing.assert_frame_equal(data, original)


def test_multiple_columns(parser, index):
    data = pd.DataFrame(
        {
            "temperature": [1.0, 2.0, 3.0],
            "status": ["ok", "warning", "error"],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert len(observations) == 6

    temperatures = [
        observation
        for observation in observations
        if observation["datastream_pos"] == "temperature"
    ]
    statuses = [
        observation
        for observation in observations
        if observation["datastream_pos"] == "status"
    ]

    assert len(temperatures) == 3
    assert len(statuses) == 3

    assert all("result_number" in observation for observation in temperatures)
    assert all("result_string" in observation for observation in statuses)


def test_unsupported_dtype_raises_parsing_error(parser, index):
    data = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2025-01-01",
                periods=3,
                freq="h",
            ),
        },
        index=index,
    )

    with pytest.raises(ParsingError, match="datetime64"):
        parser.to_observations(
            data,
            origin="test.csv",
        )


def test_error_contains_origin_and_column(parser, index):
    data = pd.DataFrame(
        {
            "unsupported": pd.date_range(
                "2025-01-01",
                periods=3,
                freq="h",
            ),
        },
        index=index,
    )

    with pytest.raises(ParsingError) as exc_info:
        parser.to_observations(
            data,
            origin="my_file.csv",
        )

    message = str(exc_info.value)

    assert "my_file.csv" in message
    assert "unsupported" in message


def test_empty_dataframe(parser, index):
    data = pd.DataFrame(index=index)

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert observations == []


def test_all_nan_column_produces_no_observations(parser, index):
    data = pd.DataFrame(
        {
            "value": [np.nan, np.nan, np.nan],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert observations == []


@pytest.mark.xfail(
    reason=(
        "The old implementation checks is_numeric_dtype before "
        "is_bool_dtype, and pandas considers bool a numeric dtype."
    ),
    strict=True,
)
def test_boolean_column_should_be_boolean(parser, index):
    data = pd.DataFrame(
        {
            "valid": [True, False, True],
        },
        index=index,
    )

    observations = parser.to_observations(
        data,
        origin="test.csv",
    )

    assert all("result_bool" in observation for observation in observations)
    assert all(
        observation["result_type"] == ObservationResultType.Bool
        for observation in observations
    )
