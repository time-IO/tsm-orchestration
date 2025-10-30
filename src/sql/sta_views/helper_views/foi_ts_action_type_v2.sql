DROP VIEW IF EXISTS foi_ts_action_type_v2 CASCADE;
CREATE OR REPLACE VIEW foi_ts_action_type_v2 AS

WITH static_action AS (
    SELECT
        o.datastream_id,
        o.result_time,
       c.label AS c_label,
        sla.id AS action_id,
        sla.begin_date,
        FALSE AS is_dynamic
    FROM public.sms_configuration_static_location_begin_action_newrange sla
    JOIN public.sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
    JOIN public.sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
    JOIN public.sms_configuration c ON c.id = dma.configuration_id
    JOIN public.sms_device d ON d.id = dma.device_id
    JOIN observation o ON o.datastream_id = dsl.datastream_id
    WHERE o.result_time <@ sla.valid_range
      AND c.is_public AND d.is_public
      AND dsl.datasource_id = '{tsm_schema}'
),
dynamic_action AS (
    SELECT
       o.datastream_id,
       o.result_time,
       c.label AS c_label,
        dla.id AS action_id,
        dla.begin_date,
        TRUE AS is_dynamic
    FROM public.sms_configuration_dynamic_location_begin_action_newrange dla
    JOIN public.sms_device_mount_action dma ON dma.configuration_id = dla.configuration_id
    JOIN public.sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
    JOIN public.sms_configuration c ON c.id = dma.configuration_id
    JOIN public.sms_device d ON d.id = dma.device_id
    JOIN observation o ON o.datastream_id = dsl.datastream_id
    WHERE c.is_public AND d.is_public
        AND dsl.datasource_id = '{tsm_schema}'
)
SELECT DISTINCT * FROM static_action
UNION ALL
SELECT * FROM dynamic_action;

