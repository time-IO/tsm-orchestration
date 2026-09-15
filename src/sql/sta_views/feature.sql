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

-- CREATE OR REPLACE VIEW "FEATURES" AS
-- SELECT
--     NULL::bigint AS "ID",
--     NULL::text AS "NAME",
--     NULL::text AS "DESCRIPTION",
--     NULL::text AS "ENCODING_TYPE",
--     NULL::jsonb AS "FEATURE",
--     NULL::jsonb AS "PROPERTIES"
-- WHERE FALSE;

CREATE OR REPLACE VIEW crns_test."FEATURES" AS
SELECT
    feature_id AS "ID",
    CONCAT(label, '_', begin_date) AS "NAME",
    CASE
        WHEN is_dynamic IS FALSE THEN 'static'
        ELSE 'dynamic'
    END AS "DESCRIPTION",
    'application/geo+json' as "ENCODING_TYPE",
    jsonb_build_object(
        'type', 'Feature',
        'geometry', jsonb_build_object(
            'type', 'Polygon',
            'coordinates', to_jsonb(coordinates)
        )
    ) AS "FEATURE",
    '{}'::jsonb AS "PROPERTIES"

FROM crns_test.foi_features_combined;

