ALTER TABLE qaqc_setting DROP COLUMN thing_id;

-- Drop the trigger first (if it exists)
DROP TRIGGER IF EXISTS trg_insert_function_parameters ON qaqc_setting_function;

-- Drop the function (if it exists)
DROP FUNCTION IF EXISTS insert_function_parameters();