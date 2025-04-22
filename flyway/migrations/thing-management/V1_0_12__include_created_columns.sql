ALTER TABLE file_parser
    ADD COLUMN created_by BIGINT NULL,
    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE NULL;

UPDATE file_parser
SET created_by = 1,
    created_at = CURRENT_TIMESTAMP
WHERE created_by IS NULL;

ALTER TABLE file_parser
    ALTER COLUMN created_by SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL;
