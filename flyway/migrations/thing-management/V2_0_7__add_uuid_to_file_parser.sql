ALTER TABLE file_parser ADD COLUMN uuid UUID NOT NULL UNIQUE;

ALTER TABLE file_parser ADD CONSTRAINT file_parser_name_project_uniq UNIQUE ("name", project_id);

ALTER TABLE mqtt_ingest ALTER COLUMN uri DROP NOT NULL;
