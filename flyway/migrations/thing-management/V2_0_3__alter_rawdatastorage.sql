ALTER TABLE thing DROP COLUMN IF EXISTS enable_raw_data_storage;
ALTER TABLE thing ADD COLUMN IF NOT EXISTS filename_pattern text;
