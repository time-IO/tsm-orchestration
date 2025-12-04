ALTER TABLE config_db.file_parser ADD COLUMN uuid UUID;
UPDATE config_db.file_parser set uuid = gen_random_uuid() WHERE uuid IS NULL;
ALTER TABLE config_db.file_parser ALTER COLUMN uuid set NOT NULL;
ALTER TABLE config_db.file_parser ALTER COLUMN uuid SET DEFAULT gen_random_uuid();
ALTER TABLE config_db.file_parser ADD CONSTRAINT parser_uuid_unique UNIQUE (uuid);