BEGIN;

SET search_path TO %(tsm_schema)s;

DROP VIEW IF EXISTS "OBSERVATIONS" CASCADE;
CREATE OR REPLACE VIEW "OBSERVATIONS" AS

SELECT DISTINCT ON ("ID")
    o.result_boolean AS "RESULT_BOOLEAN",
    o.result_quality AS "RESULT_QUALITY",
    o.result_time AS "PHENOMENON_TIME_START",
    jsonb_build_object() AS "PARAMETERS",
    dsl.device_property_id AS "DATASTREAM_ID",
    o.result_string AS "RESULT_STRING",
    o.result_type AS "RESULT_TYPE",
    o.valid_time_end AS "VALID_TIME_END",
    o.result_time AS "PHENOMENON_TIME_END",
   ('x' || MD5(crd.coordinates::text || crd.action_id))::bit(63)::bigint AS "FEATURE_ID",
    o.id AS "ID",
    o.result_json AS "RESULT_JSON",
    o.result_time AS "RESULT_TIME",
    o.result_number AS "RESULT_NUMBER",
    o.valid_time_start AS "VALID_TIME_START",
    jsonb_build_object(
        '@context', public.get_schema_org_context(),
        'jsonld.type', 'ObservationProperties',
        'dataSource', NULL
    ) AS "PROPERTIES"

FROM public.sms_datastream_link dsl
JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
JOIN public.sms_device d ON d.id = dma.device_id
JOIN public.sms_configuration c ON c.id = dma.configuration_id
JOIN ts_coordinates crd ON crd.result_time = o.result_time
WHERE c.is_public AND d.is_public AND dsl.datasource_id = %(tsm_schema)s
AND  o.result_time BETWEEN dsl.begin_date AND COALESCE(dsl.end_date, 'infinity'::timestamp)
ORDER BY "ID";

COMMIT;