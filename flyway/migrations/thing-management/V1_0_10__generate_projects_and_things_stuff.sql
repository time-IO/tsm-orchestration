------------------------------------------------------------------------
-- 1) Fix "database" sequence, insert missing "database" rows, reset seq
------------------------------------------------------------------------
SELECT setval(pg_get_serial_sequence('"database"', 'id'), COALESCE(MAX(id), 0) + 1, FALSE)
FROM "database";

INSERT INTO "database" ("schema", "user", "password", "ro_user", "ro_password")
SELECT 'schema_' || g.id,
       'db_user_' || g.id,
       'db_pass_' || g.id,
       'db_ro_user_' || g.id,
       'db_ro_pass_' || g.id
FROM generate_series(1, 10) AS g(id)
WHERE NOT EXISTS (SELECT 1
                  FROM "database"
                  WHERE "schema" = 'schema_' || g.id);

SELECT setval(pg_get_serial_sequence('"database"', 'id'), COALESCE(MAX(id), 1) + 1, FALSE)
FROM "database";


------------------------------------------------------------------------
-- 2) Fix "mqtt" sequence, insert missing "mqtt" rows, reset seq
------------------------------------------------------------------------
SELECT setval(pg_get_serial_sequence('mqtt', 'id'), COALESCE(MAX(id), 0) + 1, FALSE)
FROM "mqtt";

INSERT INTO "mqtt" ("user", "password")
SELECT 'mqtt_user_' || g.id,
       'mqtt_pass_' || g.id
FROM generate_series(1, 10) AS g(id)
WHERE NOT EXISTS (SELECT 1
                  FROM "mqtt"
                  WHERE "user" = 'mqtt_user_' || g.id);

SELECT setval(pg_get_serial_sequence('mqtt', 'id'), COALESCE(MAX(id), 1) + 1, FALSE)
FROM "mqtt";


------------------------------------------------------------------------
-- 3) Fix "project" sequence, insert new "project" rows, reset seq
------------------------------------------------------------------------
SELECT setval(pg_get_serial_sequence('project', 'id'), COALESCE(MAX(id), 0) + 1, FALSE)
FROM "project";

INSERT INTO "project" ("name", "uuid", "database_id", "mqtt_id")
SELECT 'project_' || g.id,
       gen_random_uuid(),
       (SELECT id
        FROM "database"
        ORDER BY id DESC
        LIMIT 1 OFFSET g.id - 1),
       (SELECT id
        FROM "mqtt"
        ORDER BY id DESC
        LIMIT 1 OFFSET g.id - 1)
FROM generate_series(1, 10) AS g(id)
WHERE NOT EXISTS (SELECT 1
                  FROM "project"
                  WHERE "name" = 'project_' || g.id);

SELECT setval(pg_get_serial_sequence('project', 'id'), COALESCE(MAX(id), 1) + 1, FALSE)
FROM "project";


------------------------------------------------------------------------
-- 4) Fix "file_parser" sequence, insert new rows, reset seq
------------------------------------------------------------------------
SELECT setval(pg_get_serial_sequence('file_parser', 'id'), COALESCE(MAX(id), 0) + 1, FALSE)
FROM "file_parser";

INSERT INTO "file_parser" ("file_parser_type_id", "project_id", "name", "settings")
SELECT (SELECT id
        FROM "file_parser_type"
        ORDER BY random()
        LIMIT 1),
       (SELECT id
        FROM "project"
        ORDER BY random()
        LIMIT 1),
       'parser_' || g.id,
       jsonb_build_object('config', 'random_' || g.id)
FROM generate_series(1, 50) AS g(id)
WHERE NOT EXISTS (SELECT 1
                  FROM "file_parser"
                  WHERE "name" = 'parser_' || g.id);

SELECT setval(pg_get_serial_sequence('file_parser', 'id'), COALESCE(MAX(id), 1) + 1, FALSE)
FROM "file_parser";


------------------------------------------------------------------------
-- 5) Insert 50 new "thing" rows, then link each new thing to "mqtt_ingest"
--    so there's NO possibility of duplicates in "mqtt_ingest(thing_id)"
------------------------------------------------------------------------

-- Ensure "mqtt_ingest" sequence is correct first
SELECT setval(pg_get_serial_sequence('mqtt_ingest', 'id'), COALESCE(MAX(id), 0) + 1, FALSE)
FROM "mqtt_ingest";

WITH new_things AS (
    INSERT INTO "thing" (
                         uuid,
                         name,
                         description,
                         project_id,
                         ingest_type_id,
                         enable_raw_data_storage,
                         created_at,
                         created_by
        )
        SELECT gen_random_uuid(),
               'mqtt_auto_insert_thing_' || g.id,
               'auto-created for mqtt ingest ' || g.id,
               (SELECT id
                FROM "project"
                ORDER BY random()
                LIMIT 1),
               (SELECT id
                FROM "ingest_type"
                WHERE name = 'mqtt'
                LIMIT 1),
               false,
               now(),
               (SELECT id
                FROM "user"
                ORDER BY random()
                LIMIT 1) -- pick a random user as the creator
        FROM generate_series(1, 50) g(id)
        WHERE NOT EXISTS (SELECT 1
                          FROM "thing"
                          WHERE "name" = 'mqtt_auto_insert_thing_' || g.id)
        RETURNING id)
INSERT
INTO "mqtt_ingest" ("thing_id",
                    "user",
                    "password",
                    "password_hashed",
                    "topic",
                    "uri",
                    "mqtt_device_type_id")
SELECT t.id,
       'mqtt_ingest_user_' || row_number() OVER (ORDER BY t.id),
       'mqtt_ingest_pass_' || row_number() OVER (ORDER BY t.id),
       'hashed_pass_' || row_number() OVER (ORDER BY t.id),
       'topic_' || row_number() OVER (ORDER BY t.id),
       'mqtt://broker_' || row_number() OVER (ORDER BY t.id) || '.example.com',
       (SELECT id FROM "mqtt_device_type" ORDER BY random() LIMIT 1)
FROM new_things t;

-- Fix sequence after insertion
SELECT setval(pg_get_serial_sequence('mqtt_ingest', 'id'), COALESCE(MAX(id), 1) + 1, FALSE)
FROM "mqtt_ingest";
