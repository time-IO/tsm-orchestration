ALTER TABLE rawdatastorage
    ADD COLUMN file_parser_id BIGINT NULL;

ALTER TABLE rawdatastorage
    ADD CONSTRAINT fk_rawdatastorage_file_parser FOREIGN KEY (file_parser_id)
        REFERENCES file_parser (id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;