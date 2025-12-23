DROP VIEW IF EXISTS foi_ts_action_type CASCADE;
CREATE OR REPLACE VIEW foi_ts_action_type AS

WITH
static_action AS (
    SELECT DISTINCT ON (sla.id)
        o.datastream_id,
        o.result_time,
        c.label AS c_label,
        sla.id AS action_id,
        sla.begin_date,
        FALSE AS is_dynamic,
        dma.configuration_id
    FROM public.sms_configuration_static_location_begin_action sla
    JOIN public.sms_device_mount_action dma
        ON dma.configuration_id = sla.configuration_id
    JOIN public.sms_configuration c
        ON c.id = dma.configuration_id AND c.is_public
    JOIN public.sms_device d
        ON d.id = dma.device_id AND d.is_public
    JOIN public.sms_datastream_link dsl
        ON dsl.device_mount_action_id = dma.id
        AND dsl.datasource_id = 'crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b'
    JOIN crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b.observation o
        ON o.datastream_id = dsl.datastream_id
         WHERE o.result_time >= sla.begin_date
            AND o.result_time <= COALESCE(sla.end_date, 'infinity'::timestamp)
            AND o.result_time BETWEEN dsl.begin_date AND COALESCE(dsl.end_date, 'infinity'::timestamp)


),
dynamic_action AS (
    SELECT
        o.datastream_id,
        o.result_time,
        c.label AS c_label,
        dla.id AS action_id,
        dla.begin_date,
        TRUE AS is_dynamic,
        dma.configuration_id
    FROM public.sms_configuration_dynamic_location_begin_action dla
    JOIN public.sms_device_mount_action dma
        ON dma.configuration_id = dla.configuration_id
    JOIN public.sms_configuration c
        ON c.id = dma.configuration_id AND c.is_public
    JOIN public.sms_device d ON d.id = dma.device_id AND d.is_public
    JOIN public.sms_datastream_link dsl
        ON dsl.device_mount_action_id = dma.id
        AND dsl.datasource_id = 'crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b'
    JOIN crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b.observation o
        ON o.datastream_id = dsl.datastream_id
        WHERE   o.result_time BETWEEN dsl.begin_date
          AND COALESCE(dsl.end_date, 'infinity'::timestamp)
    AND EXISTS (SELECT 1 FROM sms_configuration_dynamic_location_begin_action LIMIT 1)
)
SELECT * FROM static_action
UNION ALL
SELECT * FROM dynamic_action
;

