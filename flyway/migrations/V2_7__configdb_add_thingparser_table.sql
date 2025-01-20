SET search_path TO config_db;

CREATE TABLE "thing_parser"
(
  "id"                    BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "thing_id"              BIGINT NOT NULL,
  "file_parser_id"        BIGINT NOT NULL,
  "valid_from"            TIMESTAMP,
  "valid_to"              TIMESTAMP
);

ALTER TABLE "thing_parser"
  ADD CONSTRAINT "fk_thing_parser_thing" FOREIGN KEY ("thing_id") REFERENCES "thing" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "thing_parser"
  ADD CONSTRAINT "fk_thing_parser_file_parser" FOREIGN KEY ("thing_id") REFERENCES "file_parser" ("id") DEFERRABLE INITIALLY DEFERRED;


-- move data
INSERT INTO thing_parser (thing_id, file_parser_id)
SELECT t.id, s.file_parser_id
  FROM thing t
       JOIN s3_store s ON t.s3_store_id = s.id;

-- drop obsolete column
ALTER TABLE s3_store DROP COLUMN file_parser_id;


-- TESTING --
-- insert data

-- INSERT INTO file_parser (file_parser_type_id, name, params)
-- VALUES (1, 'DemoParser1', '{"skiprows": 1, "delimiter": ";", "skipfooter": 0, "pandas_read_csv": null, "timestamp_column": 1, "timestamp_format": "%Y/%m/%d %H:%M:%S"}');

-- INSERT INTO file_parser (file_parser_type_id, name, params)
-- VALUES (1, 'DemoParser2', '{"skiprows": 2, "delimiter": ";", "skipfooter": 0, "pandas_read_csv": null, "timestamp_column": 1, "timestamp_format": "%Y/%m/%d %H:%M:%S"}');

-- INSERT INTO file_parser (file_parser_type_id, name, params)
-- VALUES (1, 'DemoParser3', '{"skiprows": 3, "delimiter": ",", "skipfooter": 0, "pandas_read_csv": null, "timestamp_column": 1, "timestamp_format": "%Y/%m/%dT%H:%M:%S"}');


-- DELETE FROM thing_parser WHERE id=1;

-- INSERT INTO thing_parser (thing_id, file_parser_id, valid_from, valid_to)
-- VALUES (1, 1, null, '2020-01-15 10:37');

-- INSERT INTO thing_parser (thing_id, file_parser_id, valid_from, valid_to)
-- VALUES (1, 1, '2020-01-15 12:37', '2020-04-11 14:12');

-- INSERT INTO thing_parser (thing_id, file_parser_id, valid_from, valid_to)
-- VALUES (1, 1, '2020-04-11 14:12', null);

-- -- queries

-- SELECT t.id as thing_id, t.project_id, p.database_id, t.ingest_type_id, t.s3_store_id,
--        tp.file_parser_id, fp.file_parser_type_id, t.mqtt_id, m.mqtt_device_type_id,
--        t.ext_sftp_id, t.ext_api_id, ea.api_type_id
--   FROM config_db.thing t
--        LEFT JOIN config_db.project p ON t.project_id = p.id
--        LEFT JOIN config_db.thing_parser tp ON t.id = tp.thing_id
--        LEFT JOIN config_db.s3_store s3s ON t.s3_store_id = s3s.id
--        LEFT JOIN config_db.file_parser fp ON tp.file_parser_id = fp.id
--        LEFT JOIN config_db.mqtt m ON t.mqtt_id = m.id
--        LEFT JOIN config_db.ext_api ea ON t.ext_api_id = ea.id
--  WHERE t.uuid = %s AND tp.valid_to is NULL;
