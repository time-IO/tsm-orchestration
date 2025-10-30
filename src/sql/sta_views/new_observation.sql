BEGIN;

SET search_path TO %(tsm_schema)s;

DROP VIEW IF EXISTS "NEW_OBSERVATIONS" CASCADE;
CREATE OR REPLACE VIEW "NEW_OBSERVATIONS" AS

SELECT
    crd.o_id AS "ID",
    crd.result_boolean AS "RESULT_BOOLEAN",
    crd.result_quality AS "RESULT_QUALITY",
    crd.result_time AS "PHENOMENON_TIME_START",
    jsonb_build_object() AS "PARAMETERS",
    dsl.device_property_id AS "DATASTREAM_ID",
    crd.result_string AS "RESULT_STRING",
    crd.result_type AS "RESULT_TYPE",
    crd.valid_time_end AS "VALID_TIME_END",
    crd.result_time AS "PHENOMENON_TIME_END",
    CASE
        WHEN crd.coordinates IS NOT NULL THEN
        ('x' || MD5(crd.feature_id))::bit(63)::bigint
        ELSE NULL
        END AS  feature_ID,
    crd.result_json AS "RESULT_JSON",
    crd.result_time AS "RESULT_TIME",
    crd.result_number AS "RESULT_NUMBER",
    crd.valid_time_start AS "VALID_TIME_START",
    jsonb_build_object(
        '@context', public.get_schema_org_context(),
        'jsonld.type', 'ObservationProperties',
        'dataSource', NULL
    ) AS "PROPERTIES"

FROM public.sms_datastream_link dsl
JOIN obs_ts_coordinates_v2 crd ON dsl.datastream_id = crd.o_datastream_id
WHERE crd.result_time BETWEEN dsl.begin_date AND COALESCE(dsl.end_date, 'infinity'::timestamp)

ORDER BY "ID";

COMMIT;