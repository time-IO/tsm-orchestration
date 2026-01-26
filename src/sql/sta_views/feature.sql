    DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'FEATURES'
        AND table_schema = '{tsm_schema}'
        AND table_type = 'BASE TABLE')
    THEN EXECUTE 'DROP TABLE "FEATURES" CASCADE';
    ELSIF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'FEATURES'
        AND table_schema = '{tsm_schema}'
        AND table_type = 'VIEW'
        )
    THEN EXECUTE 'DROP VIEW "FEATURES" CASCADE';
    END IF;
END $$;

CREATE VIEW "FEATURES" AS
SELECT
    feature_id AS "ID",
 	CONCAT(label, '_', begin_date) AS "NAME",
 	CASE
 	    WHEN is_dynamic IS FALSE THEN 'static'
 	    ELSE 'dynamic'
 	END AS "DESCRIPTION",
    to_jsonb(format('{
          "type": "Feature",
          "geometry": {
            "type": "Polygon",
            "coordinates": %s
          }
        }', coordinates)::text) AS "FEATURE",
    '{}'::jsonb  AS "PROPERTIES"

FROM foi_ts_action_type_coord
;

