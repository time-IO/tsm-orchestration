ALTER TABLE qaqc_setting DROP COLUMN thing_id;

-- Drop the trigger first (if it exists)
DROP TRIGGER IF EXISTS trg_insert_function_parameters ON qaqc_setting_function;

-- Drop the function (if it exists)
DROP FUNCTION IF EXISTS insert_function_parameters();

-- Insert field and target datastream parameter for each function
DO $$
DECLARE
    datastream_type jsonb := '{"type": "datastream", "constraint": {}}';
    field_description varchar := 'Datastream to process';
    target_description varchar := 'Datastream to which the results are written. It will be created if it does not exist.';
BEGIN
    INSERT INTO function_parameter
    (function_id, name, description, optional, "type", default_value, position)
    VALUES
           -- flagIsolated
        (1, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 3),
        (1, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 4),
        -- flagJumps
        (2, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 4),
        (2, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 5),
        -- flagOffset
        (3, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 5),
        (3, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 6),
        -- flagPlateau
        (4, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 5),
        (4, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 6),
        -- flagRange
        (5, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 3),
        (5, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 4),
        -- flagAll
        (6, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 1),
        (6, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 2),
        -- flagUniLOF
        (7, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 11),
        (7, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 12),
        -- flagZScore
        (8, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 8),
        (8, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 9),
        -- flagByScatterLowpass
        (9, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 7),
        (9, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 8),
        -- renameField
        (11, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 2),
        (11, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 3),
        -- rolling
        (12, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 5),
        (12, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 6),
        -- transferFlags
        (12, 'field', field_description, FALSE,json_build_array(datastream_type), NULL, 3),
        (12, 'target', target_description, TRUE, json_build_array(datastream_type),NULL, 4);

END $$;