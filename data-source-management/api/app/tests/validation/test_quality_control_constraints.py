import pytest
from validation import (
    QualityControlConstraints,
    TypeConstraint,
    FunctionArgument,
    QCFunction,
)

from models.quality_control_setting import (
    QualityControlFunctionCreate,
    QualityControlFunctionArgumentCreate,
)


class TestTypeConstraintDataclass:
    def test_creation(self):
        tc = TypeConstraint(type="int", constraint={"min": 0})
        assert tc.type == "int"
        assert tc.constraint == {"min": 0}

    def test_validate_valid_value(self):
        tc = TypeConstraint(type="int", constraint={"min": 0})
        assert tc.validate(5) is True

    def test_validate_invalid_value(self):
        from validation import ConstraintViolation

        tc = TypeConstraint(type="int", constraint={"min": 0})
        with pytest.raises(ConstraintViolation):
            tc.validate(-5)

    def test_validate_unknown_type_raises(self):
        tc = TypeConstraint(type="unknown_type", constraint={})
        with pytest.raises(ValueError) as exc_info:
            tc.validate("anything")
        assert "Unknown type" in str(exc_info.value)


class TestFunctionArgumentDataclass:
    def test_validate_required_arg_provided(self):
        tc = TypeConstraint(type="str", constraint={})
        arg = FunctionArgument(
            name="test_arg",
            description="A test argument",
            optional=False,
            types=[tc],
        )
        assert arg.validate("hello") is True

    def test_validate_required_arg_missing_raises(self):
        from validation import ConstraintViolation

        tc = TypeConstraint(type="str", constraint={})
        arg = FunctionArgument(
            name="test_arg",
            description="A test argument",
            optional=False,
            types=[tc],
        )
        with pytest.raises(ConstraintViolation) as exc_info:
            arg.validate(None)
        assert "required" in str(exc_info.value).lower()

    def test_validate_optional_arg_missing(self):
        tc = TypeConstraint(type="str", constraint={})
        arg = FunctionArgument(
            name="test_arg",
            description="A test argument",
            optional=True,
            types=[tc],
        )
        assert arg.validate(None) is True

    def test_validate_wrong_type_raises(self):
        from validation import ConstraintViolation

        tc = TypeConstraint(type="int", constraint={})
        arg = FunctionArgument(
            name="test_arg",
            description="A test argument",
            optional=False,
            types=[tc],
        )
        with pytest.raises(ConstraintViolation):
            arg.validate("not an int")


class TestQCFunctionDataclass:
    def test_validate_arguments_valid(self):
        tc = TypeConstraint(type="int", constraint={})
        arg = FunctionArgument(
            name="count",
            description="A count",
            optional=False,
            types=[tc],
        )
        func = QCFunction(
            name="test_func",
            description="Test function",
            arguments=[arg],
        )
        is_valid, errors = func.validate_arguments({"count": 5})
        assert is_valid is True
        assert errors == []

    def test_validate_arguments_missing_required(self):
        tc = TypeConstraint(type="int", constraint={})
        arg = FunctionArgument(
            name="count",
            description="A count",
            optional=False,
            types=[tc],
        )
        func = QCFunction(
            name="test_func",
            description="Test function",
            arguments=[arg],
        )
        is_valid, errors = func.validate_arguments({})
        assert is_valid is False
        assert len(errors) == 1
        assert "count" in errors[0]


class TestQualityControlConstraintsGetAvailableFunctions:
    def test_returns_list(self):
        result = QualityControlConstraints.get_available_functions()
        assert isinstance(result, list)

    def test_returns_all_function_names(self):
        result = QualityControlConstraints.get_available_functions()
        assert "flagIsolated" in result
        assert "flagJumps" in result
        assert "flagRange" in result
        assert "rolling" in result
        assert len(result) == 15

    def test_returns_string_names(self):
        result = QualityControlConstraints.get_available_functions()
        for name in result:
            assert isinstance(name, str)


class TestQualityControlConstraintsGetFunctionInfo:
    def test_returns_info_for_valid_function(self):
        result = QualityControlConstraints.get_function_info("flagIsolated")
        assert result is not None
        assert "description" in result
        assert "arguments" in result

    def test_returns_none_for_unknown_function(self):
        result = QualityControlConstraints.get_function_info("unknownFunction")
        assert result is None


class TestQualityControlConstraintsValidateFunctionArguments:
    def test_valid_arguments_for_flagIsolated(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "gap_window": {"type": "offset", "value": "2min"},
            "group_window": {"type": "offset", "value": "1D"},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "flagIsolated", arguments
        )
        assert is_valid is True
        assert errors == []

    def test_unknown_function_name(self):
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "unknownFunction", {}
        )
        assert is_valid is False
        assert len(errors) == 1
        assert "Unknown QC function" in errors[0]

    def test_missing_required_argument(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "flagIsolated", arguments
        )
        assert is_valid is False
        assert any("gap_window" in e for e in errors)

    def test_wrong_type_for_argument(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "gap_window": {"type": "float", "value": 2.5},
            "group_window": {"type": "offset", "value": "1D"},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "flagIsolated", arguments
        )
        assert is_valid is False

    def test_invalid_offset_value(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "gap_window": {"type": "offset", "value": "invalid"},
            "group_window": {"type": "offset", "value": "1D"},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "flagIsolated", arguments
        )
        assert is_valid is False

    def test_flagRange_valid_min_max(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "min": {"type": "float", "value": 0.0},
            "max": {"type": "float", "value": 100.0},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "flagRange", arguments
        )
        assert is_valid is True
        assert errors == []

    def test_flagRange_min_exceeds_max(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "min": {"type": "float", "value": 100.0},
            "max": {"type": "float", "value": 0.0},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "flagRange", arguments
        )
        assert is_valid is True

    def test_flagZScore_with_optional_args(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "window": {"type": "offset", "value": "1D"},
            "thresh": {"type": "float", "value": 3.0},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "flagZScore", arguments
        )
        assert is_valid is True

    def test_rolling_valid(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "window": {"type": "offset", "value": "1D"},
            "func": {"type": "enum", "value": "mean"},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "rolling", arguments
        )
        assert is_valid is True

    def test_rolling_invalid_func(self):
        arguments = {
            "field": {"type": "datastream", "value": ["ds1"]},
            "window": {"type": "offset", "value": "1D"},
            "func": {"type": "enum", "value": "invalid_func"},
        }
        is_valid, errors = QualityControlConstraints.validate_function_arguments(
            "rolling", arguments
        )
        assert is_valid is False


class TestQualityControlConstraintsValidateSettings:
    def test_valid_settings_single_function(
        self, sample_quality_control_function_create
    ):
        settings = [sample_quality_control_function_create]

        is_valid, errors = QualityControlConstraints.validate_settings(settings)
        assert is_valid is True
        assert errors == []

    def test_invalid_settings_unknown_function(self):
        settings = [
            QualityControlFunctionCreate(
                name="unknownFunction",
                quality_control_function_arguments=[],
            )
        ]

        is_valid, errors = QualityControlConstraints.validate_settings(settings)
        assert is_valid is False
        assert any("Unknown QC function" in e for e in errors)

    def test_valid_settings_multiple_functions(self):
        settings = [
            QualityControlFunctionCreate(
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
            ),
            QualityControlFunctionCreate(
                name="flagRange",
                quality_control_function_arguments=[
                    QualityControlFunctionArgumentCreate(
                        name="field", type="datastream", input={"value": ["ds1"]}
                    ),
                    QualityControlFunctionArgumentCreate(
                        name="min", type="float", input={"value": 0.0}
                    ),
                    QualityControlFunctionArgumentCreate(
                        name="max", type="float", input={"value": 100.0}
                    ),
                ],
            ),
        ]

        is_valid, errors = QualityControlConstraints.validate_settings(settings)
        assert is_valid is True
        assert errors == []

    def test_partial_invalid_settings(self):
        settings = [
            QualityControlFunctionCreate(
                name="flagIsolated",
                quality_control_function_arguments=[
                    QualityControlFunctionArgumentCreate(
                        name="field", type="datastream", input={"value": ["ds1"]}
                    ),
                    QualityControlFunctionArgumentCreate(
                        name="gap_window", type="offset", input={"value": "2H"}
                    ),
                    QualityControlFunctionArgumentCreate(
                        name="group_window", type="offset", input={"value": "1D"}
                    ),
                ],
            ),
            QualityControlFunctionCreate(
                name="flagRange",
                quality_control_function_arguments=[
                    QualityControlFunctionArgumentCreate(
                        name="field", type="datastream", input={"value": ["ds1"]}
                    ),
                    QualityControlFunctionArgumentCreate(
                        name="min", type="float", input={"value": 0.0}
                    ),
                    QualityControlFunctionArgumentCreate(
                        name="max", type="datastream", input={"value": "invalid"}
                    ),
                ],
            ),
        ]

        is_valid, errors = QualityControlConstraints.validate_settings(settings)
        assert is_valid is False
        assert len(errors) > 0


@pytest.mark.parametrize(
    "function_name",
    [
        "processGeneric",
        "flagGeneric",
    ],
)
def test_generic_function_valid(function_name):
    settings = [
        QualityControlFunctionCreate(
            name=function_name,
            quality_control_function_arguments=[
                QualityControlFunctionArgumentCreate(
                    name="field",
                    type="datastream",
                    input={"value": ["ds1", "ds2", "ds3"]},
                ),
                QualityControlFunctionArgumentCreate(
                    name="target",
                    type="datastream",
                    input={"value": ["ds1created"]},
                ),
                QualityControlFunctionArgumentCreate(
                    name="function",
                    type="function",
                    input={"value": "(ds1 + ds2).add(arg=ds3)"},
                ),
            ],
        ),
    ]
    is_valid, errors = QualityControlConstraints.validate_settings(settings)
    assert len(errors) == 0
    assert is_valid


@pytest.mark.parametrize(
    "function_name",
    [
        "processGeneric",
        "flagGeneric",
    ],
)
def test_generic_function_invalid(function_name):
    settings = [
        QualityControlFunctionCreate(
            name=function_name,
            quality_control_function_arguments=[
                QualityControlFunctionArgumentCreate(
                    name="field", type="datastream", input={"value": ["ds1"]}
                ),
                QualityControlFunctionArgumentCreate(
                    name="target", type="datastream", input={"value": ["ds1"]}
                ),
                QualityControlFunctionArgumentCreate(
                    name="function", type="function", input={"value": "import os"}
                ),
            ],
        ),
    ]

    is_valid, errors = QualityControlConstraints.validate_settings(settings)

    assert is_valid is False
    assert len(errors) == 1
    assert f"Function '{function_name}'" in errors[0]
    assert "Argument 'function'" in errors[0]
    assert "Invalid expression:" in errors[0]
