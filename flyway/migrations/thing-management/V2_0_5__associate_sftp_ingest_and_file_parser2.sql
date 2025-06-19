ALTER TABLE external_sftp_ingest
    ADD COLUMN file_parser_id BIGINT;

ALTER TABLE external_sftp_ingest
    ADD CONSTRAINT fk_external_sftp_file_parser FOREIGN KEY (file_parser_id)
        REFERENCES file_parser (id) DEFERRABLE INITIALLY DEFERRED;