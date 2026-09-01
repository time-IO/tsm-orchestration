# validation/qc_function_definitions.py
"""
Quality Control Function Definitions
====================================
Reusable argument definitions and constraint data for QC functions.
"""

FIELD_DESCRIPTOR = "field"
TARGET_DESCRIPTOR = "target"

OFFSET_REGEX = r"^(?:\d+)?(?:B|D|W|M|Q|Y|h|min|s|ms|us|ns)?$"

OFFSET_TYPE = {"type": "offset", "constraint": {"regex": OFFSET_REGEX}}

DATASTREAM_TYPE = {"type": "datastream", "constraint": {"min": 1}}

FUNCTION_TYPE = {"type": "function", "constraint": {}}
BOOL_TYPE = {"type": "bool", "constraint": {}}

FIELD_ARG = {
    "name": FIELD_DESCRIPTOR,
    "description": "Input data stream(s).",
    "optional": False,
    "default_value": None,
    "types": [DATASTREAM_TYPE],
}

TARGET_ARG_REQUIRED = {
    "name": TARGET_DESCRIPTOR,
    "description": "Output data stream(s) to which the results are written. Defaults to field if null.",
    "optional": False,
    "default_value": None,
    "types": [DATASTREAM_TYPE],
}

TARGET_ARG_SIMPLE = {
    "name": TARGET_DESCRIPTOR,
    "description": "Output data stream(s).",
    "optional": True,
    "default_value": None,
    "types": [DATASTREAM_TYPE],
}

FLAG_ARG = {
    "name": "flag",
    "description": "Flag value used to annotate detected observations. Defaults to the BAD value of the active flagging scheme.",
    "optional": True,
    "default_value": 255.0,
    "types": [{"type": "float", "constraint": {"min": 0}}],
}

DFILTER_ARG = {
    "name": "dfilter",
    "description": "Values with flags greater than or equal to this threshold are treated as missing during processing.",
    "optional": True,
    "default_value": 0,
    "types": [{"type": "float", "constraint": {}}],
}

_definition = {
    "flagIsolated": {
        "description": "Find and flag temporally isolated data groups.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "gap_window",
                "description": "Minimum gap size required before and after a group to consider it isolated.",
                "optional": False,
                "default_value": None,
                "types": [OFFSET_TYPE],
            },
            {
                "name": "group_window",
                "description": "Maximum size of a data chunk to consider for isolation.",
                "optional": False,
                "default_value": None,
                "types": [OFFSET_TYPE],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "flagJumps": {
        "description": "Flag jumps and drops in data where the mean significantly changes.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "thresh",
                "description": "Threshold for mean difference between adjacent windows to trigger flagging.",
                "optional": False,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "window",
                "description": "Size of the rolling windows used to calculate the mean.",
                "optional": False,
                "default_value": None,
                "types": [OFFSET_TYPE],
            },
            {
                "name": "min_periods",
                "description": "Minimum observations required for a valid mean calculation.",
                "optional": True,
                "default_value": 0,
                "types": [{"type": "int", "constraint": {"min": 0}}],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "flagRange": {
        "description": "Flag values exceeding the given min-max interval.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "min",
                "description": "Lower bound for valid data.",
                "optional": False,
                "default_value": None,
                "types": [{"type": "float", "constraint": {}}],
            },
            {
                "name": "max",
                "description": "Upper bound for valid data.",
                "optional": False,
                "default_value": None,
                "types": [{"type": "float", "constraint": {}}],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "flagAll": {
        "description": "Set the given flag at all unflagged positions.",
        "arguments": [FIELD_ARG, TARGET_ARG_SIMPLE, FLAG_ARG, DFILTER_ARG],
    },
    "flagUniLOF": {
        "description": "Flag outliers using univariate Local Outlier Factor (LOF).",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "n",
                "description": "Number of periods to include in LOF calculation.",
                "optional": True,
                "default_value": 20,
                "types": [{"type": "int", "constraint": {}}],
            },
            {
                "name": "thresh",
                "description": "LOF cutoff value.",
                "optional": True,
                "default_value": "auto",
                "types": [
                    {"type": "float", "constraint": {"min": 0}},
                    {"type": "enum", "constraint": {"only": ["auto"]}},
                ],
            },
            {
                "name": "probability",
                "description": "Outlier probability cutoff.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"max": 1, "min": 0}}],
            },
            {
                "name": "corruption",
                "description": "Portion or count of data considered anomalous.",
                "optional": True,
                "default_value": None,
                "types": [
                    {"type": "float", "constraint": {"max": 1, "min": 0}},
                    {"type": "int", "constraint": {"min": 1}},
                ],
            },
            {
                "name": "algorithm",
                "description": "Algorithm for nearest neighbor calculation.",
                "optional": True,
                "default_value": "ball_tree",
                "types": [
                    {
                        "type": "enum",
                        "constraint": {
                            "only": ["ball_tree", "kd_tree", "brute", "auto"]
                        },
                    }
                ],
            },
            {
                "name": "p",
                "description": "Minkowski metric degree.",
                "optional": True,
                "default_value": 1,
                "types": [{"type": "int", "constraint": {"min": 1}}],
            },
            {
                "name": "density",
                "description": "Temporal density calculation.",
                "optional": True,
                "default_value": "auto",
                "types": [
                    {"type": "float", "constraint": {"min": 0}},
                    {"type": "enum", "constraint": {"only": ["auto"]}},
                ],
            },
            {
                "name": "fill_na",
                "description": "Fill NaNs via interpolation if True.",
                "optional": True,
                "default_value": True,
                "types": [BOOL_TYPE],
            },
            {
                "name": "slope_correct",
                "description": "Remove clusters caused by steep slopes.",
                "optional": True,
                "default_value": True,
                "types": [BOOL_TYPE],
            },
            {
                "name": "min_offset",
                "description": "Minimum value jump before and after clusters to flag.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "flagZScore": {
        "description": "Flag data points where (rolling) Z-score exceeds threshold.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "method",
                "description": "'standard' or 'modified' Z-score calculation.",
                "optional": True,
                "default_value": None,
                "types": [
                    {
                        "type": "enum",
                        "constraint": {"only": ["standard", "modified"]},
                    }
                ],
            },
            {
                "name": "window",
                "description": "Rolling window size.",
                "optional": True,
                "default_value": None,
                "types": [
                    {"type": "int", "constraint": {"min": 1}},
                    OFFSET_TYPE,
                ],
            },
            {
                "name": "thresh",
                "description": "Z-score threshold.",
                "optional": True,
                "default_value": 3,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "min_residuals",
                "description": "Minimum residual to consider a point as outlier.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "min_periods",
                "description": "Minimum valid points in a window.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "int", "constraint": {"min": 1}}],
            },
            {
                "name": "center",
                "description": "Whether to center the window.",
                "optional": True,
                "default_value": True,
                "types": [BOOL_TYPE],
            },
            {
                "name": "axis",
                "description": "Axis along which scoring is applied.",
                "optional": True,
                "default_value": 0,
                "types": [{"type": "int", "constraint": {"max": 1, "min": 0}}],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "flagByScatterLowpass": {
        "description": "Flag data chunks exceeding deviation threshold.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "window",
                "description": "Chunk size for evaluation.",
                "optional": False,
                "default_value": None,
                "types": [OFFSET_TYPE],
            },
            {
                "name": "thresh",
                "description": "Threshold for chunk deviation.",
                "optional": False,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "func",
                "description": "Aggregation function for chunk evaluation.",
                "optional": True,
                "default_value": "std",
                "types": [
                    {"type": "enum", "constraint": {"only": ["std", "var", "mad"]}}
                ],
            },
            {
                "name": "sub_window",
                "description": "Window size for sub-chunks.",
                "optional": True,
                "default_value": None,
                "types": [OFFSET_TYPE],
            },
            {
                "name": "sub_thresh",
                "description": "Threshold for sub-chunk deviation.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "min_periods",
                "description": "Minimum points required in a chunk.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "int", "constraint": {"min": 0}}],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "flagOffset": {
        "description": "Detect and flag spikes or offset value courses.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "tolerance",
                "description": "Maximum allowed difference between preceding and succeeding values.",
                "optional": False,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "window",
                "description": "Maximum duration for offset sequence.",
                "optional": False,
                "default_value": None,
                "types": [OFFSET_TYPE],
            },
            {
                "name": "thresh",
                "description": "Minimum absolute difference to consider a sequence as an offset.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "thresh_relative",
                "description": "Minimum relative change to consider a sequence as an offset.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "float", "constraint": {}}],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "flagPlateau": {
        "description": "Flag anomalous value plateaus in a time series.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "min_length",
                "description": "Minimum temporal extension of a plateau.",
                "optional": False,
                "default_value": None,
                "types": [
                    {"type": "int", "constraint": {"min": 1}},
                    OFFSET_TYPE,
                ],
            },
            {
                "name": "max_length",
                "description": "Maximum temporal extension of a plateau.",
                "optional": True,
                "default_value": None,
                "types": [
                    {"type": "int", "constraint": {"min": 1}},
                    OFFSET_TYPE,
                ],
            },
            {
                "name": "min_jump",
                "description": "Minimum difference from preceding/succeeding periods.",
                "optional": True,
                "default_value": None,
                "types": [{"type": "float", "constraint": {"min": 0}}],
            },
            {
                "name": "granularity",
                "description": "Precision of search.",
                "optional": True,
                "default_value": None,
                "types": [
                    {"type": "int", "constraint": {"min": 1}},
                    OFFSET_TYPE,
                ],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "processGeneric": {
        "description": "Process a time series using a custom function.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_REQUIRED,
            {
                "name": "function",
                "description": "Function that accepts one input series per field and returns one output series per target.",
                "optional": False,
                "default_value": None,
                "types": [FUNCTION_TYPE],
            },
        ],
    },
    "flagGeneric": {
        "description": "Flag a time series using a custom condition.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "function",
                "description": "Function that accepts one input series per field and returns one boolean output series.",
                "optional": False,
                "default_value": None,
                "types": [FUNCTION_TYPE],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "propagateFlags": {
        "description": "Extend flags to preceding or subsequent values.",
        "arguments": [FIELD_ARG, TARGET_ARG_SIMPLE, FLAG_ARG, DFILTER_ARG],
    },
    "renameField": {
        "description": "Rename field to the given name.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "new_name",
                "description": "Name to assign to the field.",
                "optional": False,
                "default_value": None,
                "types": [{"type": "str", "constraint": {}}],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "rolling": {
        "description": "Calculate a rolling-window function on the data.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "window",
                "description": "Size of the rolling window.",
                "optional": False,
                "default_value": None,
                "types": [OFFSET_TYPE],
            },
            {
                "name": "func",
                "description": "Function to apply over the rolling window.",
                "optional": False,
                "default_value": "mean",
                "types": [
                    {
                        "type": "enum",
                        "constraint": {
                            "only": [
                                "sum",
                                "mean",
                                "median",
                                "min",
                                "max",
                                "std",
                                "var",
                                "skew",
                                "kurt",
                            ]
                        },
                    }
                ],
            },
            {
                "name": "min_periods",
                "description": "Minimum points required for a valid result.",
                "optional": True,
                "default_value": 0,
                "types": [{"type": "int", "constraint": {"min": 0}}],
            },
            {
                "name": "center",
                "description": "Whether to center the window.",
                "optional": True,
                "default_value": True,
                "types": [BOOL_TYPE],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
    "transferFlags": {
        "description": "Transfer flags from one variable to another.",
        "arguments": [
            FIELD_ARG,
            TARGET_ARG_SIMPLE,
            {
                "name": "squeeze",
                "description": "Collapse history into one column.",
                "optional": True,
                "default_value": False,
                "types": [BOOL_TYPE],
            },
            {
                "name": "overwrite",
                "description": "Overwrite existing flags if True.",
                "optional": True,
                "default_value": False,
                "types": [BOOL_TYPE],
            },
            FLAG_ARG,
            DFILTER_ARG,
        ],
    },
}
