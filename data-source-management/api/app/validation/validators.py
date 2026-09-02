# validation/validators.py
import ast
import re
from typing import Any

from saqc.parsing.visitor import ConfigExpressionParser

import logging

logger = logging.getLogger("DEBUG-LOGGER")


class ConstraintError(Exception):
    """Raised when a constraint is violated."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ConstraintViolation(Exception):
    """Raised when parameter doesn't meet type/constraint requirements."""

    def __init__(
        self, param: str, expected_type: str, got_value: Any, details: str = ""
    ):
        self.param = param
        self.expected_type = expected_type
        self.got_value = got_value
        self.details = details
        super().__init__(
            f"Parameter '{param}': expected {expected_type}, "
            f"got {type(got_value).__name__}={got_value!r}. {details}"
        )


class OffsetRegex:
    """Regex patterns for offset validation."""

    PATTERN = r"^(?!$)(?:\d+)?(?:B|D|W|M|Q|Y|h|min|s|ms|us|ns)?$"
    _compiled = re.compile(PATTERN)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return bool(cls._compiled.match(value))


class TypeValidator:
    """Validates values against type constraints."""

    @staticmethod
    def validate_datastream(
        value: Any,
        constraint: dict,
        fields: list[dict],
    ) -> bool:
        """Validate datastream input (must be a list with min elements)."""
        if not isinstance(value, (list, tuple)):
            raise ConstraintViolation(
                "datastream",
                "list or tuple",
                value,
                "Must be a list of datastream references",
            )

        min_count = constraint.get("min", 1)
        if len(value) < min_count:
            raise ConstraintViolation(
                "datastream",
                f"at least {min_count} items",
                value,
                f"Requires minimum {min_count} datastream(s)",
            )
        return True

    @staticmethod
    def validate_float(
        value: Any,
        constraint: dict,
        fields: list[dict] | None = None,
    ) -> bool:
        """Validate float value against min/max constraints."""
        try:
            float_val = float(value)
        except (TypeError, ValueError):
            raise ConstraintViolation("float", "numeric value", value)

        if "min" in constraint and float_val < constraint["min"]:
            raise ConstraintViolation(
                "float",
                f"minimum {constraint['min']}",
                value,
                f"Value {float_val} is below minimum {constraint['min']}",
            )
        if "max" in constraint and float_val > constraint["max"]:
            raise ConstraintViolation(
                "float",
                f"maximum {constraint['max']}",
                value,
                f"Value {float_val} exceeds maximum {constraint['max']}",
            )
        return True

    @staticmethod
    def validate_int(
        value: Any,
        constraint: dict,
        fields: list[dict] | None = None,
    ) -> bool:
        """Validate integer value against min/max constraints."""
        try:
            int_val = int(value)
        except (TypeError, ValueError):
            raise ConstraintViolation("int", "integer value", value)

        if "min" in constraint and int_val < constraint["min"]:
            raise ConstraintViolation(
                "int",
                f"minimum {constraint['min']}",
                value,
                f"Value {int_val} is below minimum {constraint['min']}",
            )
        if "max" in constraint and int_val > constraint["max"]:
            raise ConstraintViolation(
                "int",
                f"maximum {constraint['max']}",
                value,
                f"Value {int_val} exceeds maximum {constraint['max']}",
            )
        return True

    @staticmethod
    def validate_offset(
        value: Any,
        constraint: dict,
        fields: list[dict] | None = None,
    ) -> bool:
        """Validate offset string (e.g., '2H', '1D', '30min')."""
        if not isinstance(value, str):
            raise ConstraintViolation("offset", "string", value)

        regex = constraint.get("regex")
        if regex and not re.match(regex, value):
            raise ConstraintViolation(
                "offset", "valid offset string", value, f"Must match pattern: {regex}"
            )

        # Also validate with our known patterns
        if not OffsetRegex.is_valid(value):
            raise ConstraintViolation(
                "offset",
                "valid offset string",
                value,
                "Must be a valid duration like '1H', '2D', '30min', etc.",
            )
        return True

    @staticmethod
    def validate_bool(
        value: Any,
        constraint: dict,
        fields: list[dict] | None = None,
    ) -> bool:
        """Validate boolean value."""
        if not isinstance(value, bool):
            # Also accept string representations
            if isinstance(value, str) and value.lower() in ("true", "false"):
                return True
            raise ConstraintViolation("bool", "boolean", value)
        return True

    @staticmethod
    def validate_str(
        value: Any,
        constraint: dict,
        fields: list[dict] | None = None,
    ) -> bool:
        """Validate string value."""
        if not isinstance(value, str):
            raise ConstraintViolation("str", "string", value)
        return True

    @staticmethod
    def validate_enum(
        value: Any,
        constraint: dict,
        fields: list[dict] | None = None,
    ) -> bool:
        """Validate against enum values."""
        allowed = constraint.get("only", [])
        if value not in allowed:
            raise ConstraintViolation(
                "enum",
                f"one of {allowed}",
                value,
                f"Value must be one of: {', '.join(str(x) for x in allowed)}",
            )
        return True

    @staticmethod
    def validate_generic_function(
        value: Any,
        constraint: dict,
        fields: list[dict],
    ) -> bool:
        # TODO: Implement mutability check for target
        if not isinstance(value, str):
            raise ConstraintViolation("function", "string expression", value)

        try:
            tree = ast.parse(value, mode="eval")
            parser = ConfigExpressionParser(tree)
        except Exception as e:
            raise ConstraintViolation(
                "function",
                "valid expression",
                value,
                f"Invalid expression: {e}",
            ) from e

        if len(parser.args) != len(fields):
            variable_label = (
                "input variable" if len(parser.args) == 1 else "input variables"
            )
            field_label = "field was" if len(fields) == 1 else "fields were"
            raise ConstraintViolation(
                "function",
                "one input variable per selected field",
                value,
                f"The expression uses {len(parser.args)} {variable_label}, "
                f"but {len(fields)} {field_label} selected.",
            )

        return True


# Mapping from type names to validator methods
TYPE_VALIDATORS = {
    "datastream": TypeValidator.validate_datastream,
    "float": TypeValidator.validate_float,
    "int": TypeValidator.validate_int,
    "offset": TypeValidator.validate_offset,
    "bool": TypeValidator.validate_bool,
    "str": TypeValidator.validate_str,
    "enum": TypeValidator.validate_enum,
    "function": TypeValidator.validate_generic_function,
}
