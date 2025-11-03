ALTER TABLE external_sftp_ingest DROP COLUMN IF EXISTS file_parser_id;
ALTER TABLE rawdatastorage ADD COLUMN IF NOT EXISTS file_parser_id INT;

ALTER TABLE rawdatastorage ADD CONSTRAINT fk_file_parser FOREIGN KEY (file_parser_id) REFERENCES file_parser(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
