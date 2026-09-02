import pytest
from validation import (
    ConstraintViolation,
    ConstraintError,
    OffsetRegex,
    TypeValidator,
    TYPE_VALIDATORS,
)


class TestOffsetRegex:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1B", True),
            ("2D", True),
            ("30W", True),
            ("1M", True),
            ("1Q", True),
            ("1Y", True),
            ("1h", True),
            ("1min", True),
            ("1s", True),
            ("1ms", True),
            ("1us", True),
            ("1ns", True),
            ("", False),
            ("1", True),
            ("1X", False),
            ("abc", False),
            ("1H2D", False),
        ],
    )
    def test_is_valid(self, value, expected):
        assert OffsetRegex.is_valid(value) is expected


class TestConstraintViolation:
    def test_exception_attributes(self):
        exc = ConstraintViolation("param", "int", 42, "must be positive")
        assert exc.param == "param"
        assert exc.expected_type == "int"
        assert exc.got_value == 42
        assert exc.details == "must be positive"

    def test_exception_message(self):
        exc = ConstraintViolation("param", "int", 42, "must be positive")
        assert "param" in str(exc)
        assert "int" in str(exc)
        assert "42" in str(exc)


class TestConstraintError:
    def test_exception_attributes(self):
        exc = ConstraintError("field", "is required")
        assert exc.field == "field"
        assert exc.message == "is required"

    def test_exception_message(self):
        exc = ConstraintError("field", "is required")
        assert "field" in str(exc)
        assert "is required" in str(exc)


class TestTypeValidatorValidateDatastream:
    def test_valid_list(self, sample_datastream_refs):
        constraint = {"min": 1}
        assert (
            TypeValidator.validate_datastream(sample_datastream_refs, constraint, [])
            is True
        )

    def test_valid_tuple(self):
        constraint = {"min": 1}
        assert TypeValidator.validate_datastream(("ds1", "ds2"), constraint, []) is True

    def test_invalid_not_list_or_tuple(self):
        constraint = {"min": 1}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_datastream("not a list", constraint, [])
        assert "datastream" in str(exc_info.value).lower()
        assert "list or tuple" in str(exc_info.value)

    def test_below_min_count(self):
        constraint = {"min": 3}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_datastream(["ds1"], constraint, [])
        assert "at least 3 items" in str(exc_info.value)

    def test_min_count_exactly_met(self):
        constraint = {"min": 2}
        assert TypeValidator.validate_datastream(["ds1", "ds2"], constraint, []) is True

    def test_default_min_is_one(self):
        assert TypeValidator.validate_datastream(["ds1"], {}, []) is True
        with pytest.raises(ConstraintViolation):
            TypeValidator.validate_datastream([], {}, [])


class TestTypeValidatorValidateFloat:
    def test_valid_float(self):
        constraint = {}
        assert TypeValidator.validate_float(3.14, constraint, []) is True

    def test_valid_int_converts_to_float(self):
        constraint = {}
        assert TypeValidator.validate_float(42, constraint, []) is True

    def test_valid_string_number(self):
        constraint = {}
        assert TypeValidator.validate_float("3.14", constraint, []) is True

    def test_valid_with_min_constraint(self):
        constraint = {"min": 0.0}
        assert TypeValidator.validate_float(1.5, constraint, []) is True

    def test_valid_with_max_constraint(self):
        constraint = {"max": 100.0}
        assert TypeValidator.validate_float(50.0, constraint, []) is True

    def test_valid_with_min_max_constraint(self):
        constraint = {"min": 0.0, "max": 100.0}
        assert TypeValidator.validate_float(50.0, constraint, []) is True

    def test_below_min_constraint(self):
        constraint = {"min": 10.0}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_float(5.0, constraint, [])
        assert "minimum 10.0" in str(exc_info.value)
        assert "5.0" in str(exc_info.value)

    def test_above_max_constraint(self):
        constraint = {"max": 10.0}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_float(15.0, constraint, [])
        assert "maximum 10.0" in str(exc_info.value)
        assert "15.0" in str(exc_info.value)

    def test_invalid_non_numeric_string(self):
        constraint = {}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_float("not a number", constraint, [])
        assert "numeric value" in str(exc_info.value)

    def test_invalid_none(self):
        constraint = {}
        with pytest.raises(ConstraintViolation):
            TypeValidator.validate_float(None, constraint, [])


class TestTypeValidatorValidateInt:
    def test_valid_int(self):
        constraint = {}
        assert TypeValidator.validate_int(42, constraint, []) is True

    def test_valid_float_truncates(self):
        constraint = {}
        assert TypeValidator.validate_int(42.9, constraint, []) is True

    def test_valid_string_number(self):
        constraint = {}
        assert TypeValidator.validate_int("42", constraint, []) is True

    def test_valid_with_min_constraint(self):
        constraint = {"min": 0}
        assert TypeValidator.validate_int(1, constraint, []) is True

    def test_valid_with_max_constraint(self):
        constraint = {"max": 100}
        assert TypeValidator.validate_int(50, constraint, []) is True

    def test_below_min_constraint(self):
        constraint = {"min": 10}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_int(5, constraint, [])
        assert "minimum 10" in str(exc_info.value)

    def test_above_max_constraint(self):
        constraint = {"max": 10}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_int(15, constraint, [])
        assert "maximum 10" in str(exc_info.value)

    def test_invalid_non_numeric_string(self):
        constraint = {}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_int("not a number", constraint, [])
        assert "integer value" in str(exc_info.value)

    def test_invalid_none(self):
        constraint = {}
        with pytest.raises(ConstraintViolation):
            TypeValidator.validate_int(None, constraint, [])


class TestTypeValidatorValidateOffset:
    @pytest.mark.parametrize(
        "value",
        [
            "1h",
            "2D",
            "30min",
            "1Y",
            "1M",
            "1W",
            "100h",
        ],
    )
    def test_valid_offset_strings(self, value):
        constraint = {
            "regex": r"^(?:\d+)?(?:B|D|W|M|Q|Y|h|min|s|ms|us|ns)?$"
        }
        assert TypeValidator.validate_offset(value, constraint) is True

    def test_invalid_offset_type(self):
        constraint = {}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_offset(123, constraint, [])
        assert "offset" in str(exc_info.value).lower()
        assert "string" in str(exc_info.value)

    def test_invalid_offset_not_match_regex(self):
        constraint = {"regex": r"^\d+H$"}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_offset("1D", constraint, [])
        assert "offset" in str(exc_info.value).lower()
        assert "pattern" in str(exc_info.value)

    def test_invalid_offset_not_recognized(self):
        constraint = {}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_offset("1X", constraint, [])
        assert "offset" in str(exc_info.value).lower()


class TestTypeValidatorValidateBool:
    def test_valid_true(self):
        constraint = {}
        assert TypeValidator.validate_bool(True, constraint, []) is True

    def test_valid_false(self):
        constraint = {}
        assert TypeValidator.validate_bool(False, constraint, []) is True

    def test_valid_string_true(self):
        constraint = {}
        assert TypeValidator.validate_bool("true", constraint, []) is True
        assert TypeValidator.validate_bool("TRUE", constraint, []) is True

    def test_valid_string_false(self):
        constraint = {}
        assert TypeValidator.validate_bool("false", constraint, []) is True
        assert TypeValidator.validate_bool("FALSE", constraint, []) is True

    def test_invalid_string_other(self):
        constraint = {}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_bool("yes", constraint, [])
        assert "bool" in str(exc_info.value).lower()

    def test_invalid_int(self):
        constraint = {}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_bool(1, constraint, [])
        assert "bool" in str(exc_info.value).lower()


class TestTypeValidatorValidateStr:
    def test_valid_string(self):
        constraint = {}
        assert TypeValidator.validate_str("hello", constraint, []) is True

    def test_valid_empty_string(self):
        constraint = {}
        assert TypeValidator.validate_str("", constraint, []) is True

    def test_invalid_not_string(self):
        constraint = {}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_str(123, constraint, [])
        assert "str" in str(exc_info.value).lower()
        assert "string" in str(exc_info.value)

    def test_invalid_none(self):
        constraint = {}
        with pytest.raises(ConstraintViolation):
            TypeValidator.validate_str(None, constraint, [])


class TestTypeValidatorValidateEnum:
    def test_valid_value_in_list(self):
        constraint = {"only": ["red", "green", "blue"]}
        assert TypeValidator.validate_enum("red", constraint, []) is True

    def test_valid_int_in_list(self):
        constraint = {"only": [1, 2, 3]}
        assert TypeValidator.validate_enum(2, constraint, []) is True

    def test_invalid_value_not_in_list(self):
        constraint = {"only": ["red", "green", "blue"]}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_enum("yellow", constraint, [])
        assert "enum" in str(exc_info.value).lower()
        assert "red, green, blue" in str(exc_info.value)

    def test_invalid_empty_list(self):
        constraint = {"only": []}
        with pytest.raises(ConstraintViolation) as exc_info:
            TypeValidator.validate_enum("anything", constraint, [])
        assert "enum" in str(exc_info.value).lower()
        assert "[]" in str(exc_info.value)


class TestTypeValidatorsMapping:
    def test_all_type_names_present(self):
        expected_types = [
            "datastream",
            "float",
            "int",
            "offset",
            "bool",
            "str",
            "enum",
            "function",
        ]
        assert set(TYPE_VALIDATORS.keys()) == set(expected_types)

    def test_validator_callable(self):
        for type_name, validator in TYPE_VALIDATORS.items():
            assert callable(validator)
