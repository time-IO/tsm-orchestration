"""
Quality Control Function Constraints
====================================
Defines all quality control functions with their argument constraints.
Validates incoming parameters against these constraints.
"""

from typing import Any, List, Dict
from dataclasses import dataclass, field

from .validators import (
    TYPE_VALIDATORS,
    ConstraintViolation,
)
from .qc_function_definitions import _definition, FIELD_DESCRIPTOR


@dataclass
class TypeConstraint:
    """Defines a valid type and its constraints for a parameter."""

    type: str
    constraint: dict = field(default_factory=dict)

    def validate(self, value: Any) -> bool:
        """Validate a value against this type constraint."""
        validator = TYPE_VALIDATORS.get(self.type)
        if not validator:
            raise ValueError(f"Unknown type: {self.type}")
        return validator(value, self.constraint)


@dataclass
class FunctionArgument:
    """Defines a parameter for a quality control function."""

    name: str
    description: str
    optional: bool
    default_value: Any = None
    types: list[TypeConstraint] = field(default_factory=list)

    def validate(self, value: Any) -> bool:
        """Validate a value for this argument."""
        # Check if value is None for optional args
        if value is None:
            if self.optional:
                return True
            raise ConstraintViolation(
                self.name, "non-null value", None, "This parameter is required"
            )

        # Try each valid type
        for type_constraint in self.types:
            try:
                return type_constraint.validate(value)
            except ConstraintViolation:
                continue

        # None of the types matched
        expected_types = [t.type for t in self.types]
        raise ConstraintViolation(
            self.name,
            f"one of {expected_types}",
            value,
            f"Could not validate against any of: {expected_types}",
        )


@dataclass
class QCFunction:
    """Defines a quality control function with its parameters."""

    name: str
    description: str
    arguments: list[FunctionArgument] = field(default_factory=list)

    def validate_arguments(self, provided_args: dict) -> tuple[bool, list[str]]:
        """
        Validate provided arguments against function constraints.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        for arg in self.arguments:
            value = provided_args.get(arg.name)

            # Check for missing required arguments
            if value is None and not arg.optional:
                errors.append(
                    f"Missing required argument '{arg.name}': {arg.description}"
                )
                continue

            # Validate if provided
            if value is not None:
                try:
                    arg.validate(value)
                except ConstraintViolation as e:
                    errors.append(str(e))

        return len(errors) == 0, errors


class QualityControlConstraints:
    """
    Registry of all quality control function constraints.
    Provides validation and lookup functionality.
    """

    @classmethod
    def get_available_functions(cls) -> list[str]:
        """Return list of all available QC function names."""
        return list(_definition.keys())

    @classmethod
    def get_function_info(cls, function_name: str) -> dict | None:
        """Get function description and argument info."""
        return _definition.get(function_name)

    @classmethod
    def validate_function_arguments(
        cls, function_name: str, arguments: dict
    ) -> tuple[bool, list[str]]:
        """
        Validate arguments for a specific QC function.

        Args:
            function_name: Name of the QC function
            arguments: Dictionary of argument { "name": {"type": ..., "value": ...},... }

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        func_info = cls.get_function_info(function_name)
        if not func_info:
            return False, [f"Unknown QC function: '{function_name}'"]

        fields = arguments.get(FIELD_DESCRIPTOR, {}).get("value") or []

        func_info_arguments = func_info["arguments"]

        errors = []

        try:
            cls.validate_input_keys(arguments, func_info_arguments)
        except ValueError as exc:
            errors.append(str(exc))

        for arg_def in func_info["arguments"]:

            arg_name = arg_def["name"]

            # Get the provided argument data
            arg_data = arguments.get(arg_name)

            # Check required arguments
            if arg_data is None:
                if not arg_def["optional"]:
                    errors.append(f"Missing required argument '{arg_name}'")
                continue

            # Extract type and value from the argument data
            arg_type = arg_data.get("type")
            arg_value = arg_data.get("value")

            # Check if the provided type matches one of the allowed types
            allowed_types = [t["type"] for t in arg_def["types"]]

            if arg_type not in allowed_types:
                errors.append(
                    f"Argument '{arg_name}': expected type in {allowed_types}, got '{arg_type}'"
                )
                continue

            # Validate the value based on its type
            if arg_value is None:
                errors.append(f"Argument '{arg_name}': missing value")
                continue

            for type_def in arg_def["types"]:
                if type_def["type"] != arg_type:
                    continue

                try:
                    validator = TYPE_VALIDATORS.get(arg_type)
                    if validator:
                        validator(
                            value=arg_value,
                            constraint=type_def.get("constraint", {}),
                            fields=fields,
                        )
                        break
                except ConstraintViolation as e:
                    errors.append(f"Argument '{arg_name}': {e.details or str(e)}")
                    break

        return len(errors) == 0, errors

    @classmethod
    def validate_settings(
        cls, quality_control_functions: list
    ) -> tuple[bool, list[str]]:
        """
        Validate quality control settings from Pydantic/SQLModel objects.

        Args:
            quality_control_functions: List of QualityControlFunctionCreate objects
                                       Each has: name, quality_control_function_arguments

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        for idx, func in enumerate(quality_control_functions):
            func_name = func.name

            # Check if function exists in our constraints
            func_info = _definition.get(func_name)
            if not func_info:
                errors.append(
                    f"Function at index {idx}: Unknown QC function '{func_name}'"
                )
                continue

            # Build a dict of provided arguments for validation
            # Include type + input value for proper validation
            provided_args = {}
            for arg in func.quality_control_function_arguments:
                provided_args[arg.name] = {
                    "type": arg.type,
                    "value": arg.input.get("value"),
                }

            # Validate the arguments
            is_valid, arg_errors = cls.validate_function_arguments(
                func_name, provided_args
            )

            # Prefix errors with function index/name
            for error in arg_errors:
                errors.append(f"Function '{func_name}': {error}")

        return len(errors) == 0, errors

    @classmethod
    def validate_input_keys(
        cls, data: Dict[str, Any], schema: List[Dict[str, Any]]
    ) -> None:
        """
        Validate that every top‑level key in ``data`` exists in the schema under the
        field ``name``.

        Parameters
        ----------
        data: dict
            The JSON‑like payload you want to check (e.g. ``{'field': …, 'flag': …}``).
        schema: list[dict]
            List of parameter definitions.
            Each entry must contain a ``name`` key that holds the allowed name.

        Raises
        ------
        ValueError
            If a key in ``data`` is not present among the allowed ``name`` values.
        """
        # Build a set of all allowed names – O(1) look‑ups.
        allowed_names = {entry["name"] for entry in schema}

        # Check each key in the incoming payload.
        for key in data:
            if key not in allowed_names:
                raise ValueError(
                    f"Unexpected key “{key}”. "
                    f"Allowed keys are: {sorted(allowed_names)}"
                )
