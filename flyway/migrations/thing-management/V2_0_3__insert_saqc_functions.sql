
INSERT INTO function (id, name, description) VALUES
(1, 'flagIsolated', 'Find and flag temporally isolated data groups.'),
(2, 'flagJumps', 'Flag jumps and drops in data where the mean significantly changes.'),
(3, 'flagOffset', 'Detect and flag spikes or offset value courses in data.'),
(4, 'flagPlateau', 'Flag anomalous value plateaus in a time series.'),
(5, 'flagRange', 'Flag values exceeding the given min-max interval.'),
(6, 'flagAll', 'Set the given flag at all unflagged positions.'),
(7, 'flagUniLOF', 'Flag outliers using univariate Local Outlier Factor (LOF).'),
(8, 'flagZScore', 'Flag data points where (rolling) Z-score exceeds threshold.'),
(9, 'flagByScatterLowpass', 'Flag data chunks exceeding a deviation threshold.'),
(10, 'propagateFlags', 'Extend existing flags to preceding or subsequent values.'),
(11, 'renameField', 'Rename field to the given name.'),
(12, 'rolling', 'Calculate a rolling-window function on the data.'),
(13, 'transferFlags', 'Transfer flags from one variable to another.');

INSERT INTO function_parameter (function_id, name, description, optional, type, default_value, position) VALUES
-- flagIsolated
(1, 'gap_window', 'Minimum gap size required before and after a group to consider it isolated.', false, 'interval', NULL, 1),
(1, 'group_window', 'Maximum size of a data chunk to consider for isolation.', false, 'interval', NULL, 2),
-- flagJumps
(2, 'thresh', 'Threshold for mean difference between adjacent windows to trigger flagging.', false, 'float>=0', NULL, 1),
(2, 'window', 'Size of the rolling windows used to calculate the mean.', false, 'interval', NULL, 2),
(2, 'min_periods', 'Minimum observations required for a valid mean calculation.', true, 'int>=0', '0', 3),
-- flagOffset
(3, 'tolerance', 'Maximum allowed difference between preceding and succeeding values.', false, 'float>=0', NULL, 1),
(3, 'window', 'Maximum duration for the offset sequence.', false, 'interval', NULL, 2),
(3, 'thresh', 'Minimum absolute difference to consider a sequence as an offset.', true, 'float>0', NULL, 3),
(3, 'thresh_relative', 'Minimum relative change to consider a sequence as an offset.', true, 'float', NULL, 4),
-- flagPlateau
(4, 'min_length', 'Minimum temporal extension of a plateau.', false, 'int>0 | interval', NULL, 1),
(4, 'max_length', 'Maximum temporal extension of a plateau.', TRUE, ' int>0 | interval', NULL, 2),
(4, 'min_jump', 'Minimum difference from preceding/succeeding periods.', true, 'float>=0', NULL, 3),
(4, 'granularity', 'Precision of the search.', true, 'int>0 | interval', NULL, 4),
-- flagRange
(5, 'min', 'Lower bound for valid data.', true, 'float', '-Infinity', 1),
(5, 'max', 'Upper bound for valid data.', true, 'float', 'Infinity', 2),
-- flagUniLOF
(7, 'n', 'Number of periods to include in LOF calculation.', true, 'int', '20', 1),
(7, 'thresh', 'LOF cutoff value.', true, 'float>0 | Literal[auto]', 'auto', 2),
(7, 'probability', 'Outlier probability cutoff.', true, 'float[0, 1]', NULL, 3),
(7, 'corruption', 'Portion or count of data considered anomalous.', true, 'float[0, 1] | int>0', NULL, 4),
(7, 'algorithm', 'Algorithm for nearest neighbor calculation.', true, 'Literal["ball_tree", "kd_tree", "brute", "auto"]', 'ball_tree', 5),
(7, 'p', 'Minkowski metric degree.', true, 'int>0', '1', 6),
(7, 'density', 'Temporal density calculation.', true, 'float>0 | Literal["auto"]', 'auto', 7),
(7, 'fill_na', 'Fill NaNs via interpolation if True.', true, 'boolean', 'true', 8),
(7, 'slope_correct', 'Remove clusters caused by steep slopes.', true, 'boolean', 'true', 9),
(7, 'min_offset', 'Minimum value jump before and after clusters to flag.', true, 'float>0', NULL, 10),
-- flagZScore
(8, 'method', '''standard'' or ''modified'' Z-score calculation.', true, 'Literal["standard", "modified"]', 'standard', 1),
(8, 'window', 'Rolling window size.', true, 'interval | int >= 0', NULL, 2),
(8, 'thresh', 'Z-score threshold.', true, 'float>0', '3', 3),
(8, 'min_residuals', 'Minimum residual to consider a point as outlier.', true, 'float>=0', NULL, 4),
(8, 'min_periods', 'Minimum valid points in a window.', true, 'int>0', NULL, 5),
(8, 'center', 'Whether to center the window.', true, 'boolean', 'true', 6),
(8, 'axis', 'Axis along which scoring is applied.', true, 'int[0, 1]', '0', 7),
-- flagByScatterLowpass
(9, 'window', 'Chunk size for evaluation.', false, 'interval', NULL, 1),
(9, 'thresh', 'Threshold for chunk deviation.', false, 'float>=0', NULL, 2),
(9, 'func', 'Aggregation function for chunk evaluation.', true, 'Literal["std", "var", "mad"]', 'std', 3),
(9, 'sub_window', 'Window size for sub-chunks.', true, 'interval', NULL, 4),
(9, 'sub_thresh', 'Threshold for sub-chunk deviation.', true, 'float>=0', NULL, 5),
(9, 'min_periods', 'Minimum points required in a chunk.', true, 'int>=0', NULL, 6),
-- renameField
(11, 'new_name', 'Name to assign to the field.', false, 'str', NULL, 1),
-- rolling
(12, 'window', 'Size of the rolling window.', false, 'interval', NULL, 1),
(12, 'func', 'Function to apply over the rolling window.', false, 'Literal["sum", "mean", "median", "min", "max", "std", "var", "skew", "kurt"]', 'mean', 2),
(12, 'min_periods', 'Minimum points required for a valid result.', true, 'int>0', '0', 3),
(12, 'center', 'Whether to center the window.', true, 'boolean', 'true', 4),
-- transferFlags
(13, 'squeeze', 'Collapse history into one column.', true, 'boolean', 'false', 1),
(13, 'overwrite', 'Overwrite existing flags if True.', true, 'boolean', 'false', 2);
