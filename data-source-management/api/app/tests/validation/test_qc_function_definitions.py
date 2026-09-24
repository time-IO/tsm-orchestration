from validation.qc_function_definitions import (
    OFFSET_REGEX,
    OFFSET_TYPE,
    DATASTREAM_TYPE,
    BOOL_TYPE,
    _definition,
)


class TestOffsetRegex:
    def test_is_valid_pattern(self):
        import re

        compiled = re.compile(OFFSET_REGEX)
        assert compiled.match("1s") is not None
        assert compiled.match("2D") is not None
        assert compiled.match("30min") is not None
        assert compiled.match("invalid") is None


class TestPredefinedTypes:
    def test_offset_type_structure(self):
        assert OFFSET_TYPE["type"] == "offset"
        assert "constraint" in OFFSET_TYPE
        assert "regex" in OFFSET_TYPE["constraint"]

    def test_datastream_type_structure(self):
        assert DATASTREAM_TYPE["type"] == "datastream"
        assert "constraint" in DATASTREAM_TYPE
        assert DATASTREAM_TYPE["constraint"]["min"] == 1

    def test_bool_type_structure(self):
        assert BOOL_TYPE["type"] == "bool"
        assert "constraint" in BOOL_TYPE


class TestDefinition:
    def test_definition_is_not_empty(self):
        assert len(_definition) > 0

    def test_all_functions_have_description(self):
        for func_name, func_def in _definition.items():
            assert "description" in func_def
            assert func_def["description"]

    def test_all_functions_have_arguments(self):
        for func_name, func_def in _definition.items():
            assert "arguments" in func_def
            assert isinstance(func_def["arguments"], list)

    def test_all_arguments_have_required_fields(self):
        for func_name, func_def in _definition.items():
            for arg in func_def["arguments"]:
                assert "name" in arg
                assert "description" in arg
                assert "optional" in arg
                assert "types" in arg

    def test_all_arguments_have_valid_types(self):
        for func_name, func_def in _definition.items():
            for arg in func_def["arguments"]:
                assert isinstance(arg["types"], list)
                assert len(arg["types"]) > 0
                for type_def in arg["types"]:
                    assert "type" in type_def
                    assert "constraint" in type_def

    def test_flagIsolated_arguments(self):
        func_def = _definition["flagIsolated"]
        arg_names = [a["name"] for a in func_def["arguments"]]
        assert "field" in arg_names
        assert "gap_window" in arg_names
        assert "group_window" in arg_names

    def test_flagRange_arguments(self):
        func_def = _definition["flagRange"]
        arg_names = [a["name"] for a in func_def["arguments"]]
        assert "field" in arg_names
        assert "min" in arg_names
        assert "max" in arg_names

    def test_rolling_arguments(self):
        func_def = _definition["rolling"]
        arg_names = [a["name"] for a in func_def["arguments"]]
        assert "window" in arg_names
        assert "func" in arg_names

    def test_no_duplicate_argument_names_within_function(self):
        for func_name, func_def in _definition.items():
            arg_names = [a["name"] for a in func_def["arguments"]]
            assert len(arg_names) == len(
                set(arg_names)
            ), f"Duplicate args in {func_name}"
