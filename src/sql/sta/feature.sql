BEGIN;

SET search_path TO %(tsm_schema)s;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'FEATURES'
        AND table_schema = %(tsm_schema)s
        AND table_type = 'BASE TABLE')
    THEN EXECUTE 'DROP TABLE "FEATURES" CASCADE';
    ELSIF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'FEATURES'
        AND table_schema = %(tsm_schema)s
        AND table_type = 'VIEW'
        )
    THEN EXECUTE 'DROP VIEW "FEATURES" CASCADE';
    END IF;
END $$;
CREATE TABLE "FEATURES" (
  "ID" serial,
  "NAME" text,
  "DESCRIPTION" text,
  "ENCODING_TYPE" text,
  "FEATURE" jsonb,
  "PROPERTIES" jsonb
);

COMMIT;