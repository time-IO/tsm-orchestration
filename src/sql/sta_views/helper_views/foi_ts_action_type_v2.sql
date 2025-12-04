
    DROP VIEW IF EXISTS foi_ts_action_type_v2 CASCADE;
CREATE OR REPLACE VIEW foi_ts_action_type_v2 AS

WITH has_dynamic AS (
    SELECT EXISTS (
        SELECT 1 FROM sms_configuration_dynamic_location_begin_action LIMIT 1
    ) AS flag
),
static_action AS (
    SELECT DISTINCT ON (sla.id)
        o.datastream_id,
        o.result_time,
        c.label AS c_label,
        sla.id AS action_id,
        sla.begin_date,
        FALSE AS is_dynamic
    FROM public.sms_configuration_static_location_begin_action sla
    JOIN public.sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
    JOIN public.sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
    JOIN public.sms_configuration c ON c.id = dma.configuration_id
    JOIN public.sms_device d ON d.id = dma.device_id
    JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation o ON o.datastream_id = dsl.datastream_id
    WHERE o.result_time >= sla.begin_date AND (o.result_time <= sla.end_date OR sla.end_date IS NULL)
      AND c.is_public AND d.is_public
      AND dsl.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
),
dynamic_action AS (
    SELECT
        o.datastream_id,
        o.result_time,
        c.label AS c_label,
        dla.id AS action_id,
        dla.begin_date,
        TRUE AS is_dynamic
    FROM has_dynamic
    CROSS JOIN public.sms_configuration_dynamic_location_begin_action dla
    JOIN public.sms_device_mount_action dma ON dma.configuration_id = dla.configuration_id
    JOIN public.sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
    JOIN public.sms_configuration c ON c.id = dma.configuration_id
    JOIN public.sms_device d ON d.id = dma.device_id
    JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation o ON o.datastream_id = dsl.datastream_id
    WHERE has_dynamic.flag = TRUE
        AND c.is_public AND d.is_public
        AND dsl.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
)
SELECT * FROM static_action
UNION ALL
SELECT * FROM dynamic_action;

