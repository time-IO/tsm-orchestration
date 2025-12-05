ALTER TABLE file_parser ADD COLUMN uuid UUID NOT NULL UNIQUE;

ALTER TABLE file_parser ADD CONSTRAINT file_parser_name_project_uniq UNIQUE ("name", project_id);

ALTER TABLE mqtt_ingest ALTER COLUMN uri DROP NOT NULL;

INSERT INTO external_api_type (name)
VALUES ('uba'::varchar(200)),
       ('tsystems'::varchar(200));

INSERT INTO mqtt_device_type (name)
VALUES ('chirpstack_generic'::varchar(200));