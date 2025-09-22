ALTER TABLE external_sftp_ingest DROP COLUMN IF EXISTS file_parser_id;
ALTER TABLE rawdatastorage ADD COLUMN IF NOT EXISTS file_parser_id INT;
