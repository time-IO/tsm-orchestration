ALTER TABLE external_sftp_ingest DROP COLUMN IF EXISTS file_name_pattern;
ALTER TABLE rawdatastorage ADD COLUMN IF NOT EXISTS file_name_pattern text;
