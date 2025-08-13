BEGIN;

SET search_path TO %(tsm_schema)s;

DROP VIEW IF EXISTS "ts_action_type" CASCADE;
CREATE OR REPLACE VIEW "ts_action_type" AS
WITH ts_action_type_unfiltered AS (
    SELECT DISTINCT obs.result_time,
        CASE
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.static_ranges) THEN 'static'
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.dynamic_ranges) THEN 'dynamic'
        END AS "action_type",
        CASE
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.static_ranges) THEN ranges.static_id
            WHEN tstzrange(obs.result_time,obs.result_time, '[]') <@ any(ranges.dynamic_ranges) THEN ranges.dynamic_id
        END AS "action_id"
    FROM public.sms_datastream_link dsl
    JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
    JOIN static_dynamic_tsranges ranges ON ranges.configuration_id = dma.configuration_id
    JOIN observation obs ON obs.datastream_id = dsl.datastream_id
)
SELECT result_time, action_type, action_id FROM ts_action_type_unfiltered
WHERE action_type IS NOT NULL AND action_id IS NOT NULL;

COMMIT;