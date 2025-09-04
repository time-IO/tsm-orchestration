ALTER TABLE thing DROP COLUMN IF EXISTS enable_raw_data_storage;
ALTER TABLE thing ADD COLUMN IF NOT EXISTS filename_pattern text;
ALTER TABLE external_sftp_ingest DROP COLUMN IF EXISTS file_name_pattern;
ALTER TABLE rawdatastorage ADD COLUMN IF NOT EXISTS file_name_pattern VARCHAR(128) ;
