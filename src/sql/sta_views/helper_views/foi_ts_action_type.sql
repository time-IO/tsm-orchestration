DROP VIEW IF EXISTS foi_ts_action_type CASCADE;
CREATE OR REPLACE VIEW foi_ts_action_type AS

WITH
static_action AS (
    SELECT DISTINCT ON (sla.id)
        sla.id AS action_id,
        FALSE AS is_dynamic,
        o.datastream_id,
        o.result_time,
        c.label AS c_label,
        sla.begin_date,
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
        AND dsl.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
    JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation o
        ON o.datastream_id = dsl.datastream_id
         WHERE o.result_time >= sla.begin_date
            AND o.result_time <= COALESCE(sla.end_date, 'infinity'::timestamp)
--             AND o.result_time BETWEEN dsl.begin_date AND COALESCE(dsl.end_date, 'infinity'::timestamp)



),
dynamic_action AS (
    SELECT
        dla.id AS action_id,
        TRUE AS is_dynamic,
        o.datastream_id,
        o.result_time,
        c.label AS c_label,
        dla.begin_date,
        dma.configuration_id
    FROM public.sms_configuration_dynamic_location_begin_action dla
    JOIN public.sms_device_mount_action dma
        ON dma.configuration_id = dla.configuration_id
    JOIN public.sms_configuration c
        ON c.id = dma.configuration_id AND c.is_public
    JOIN public.sms_device d ON d.id = dma.device_id AND d.is_public
    JOIN public.sms_datastream_link dsl
        ON dsl.device_mount_action_id = dma.id
        AND dsl.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
    JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation o
        ON o.datastream_id = dsl.datastream_id
--         WHERE   o.result_time BETWEEN dsl.begin_date
--           AND COALESCE(dsl.end_date, 'infinity'::timestamp)

)
SELECT * FROM static_action
UNION ALL
SELECT * FROM dynamic_action
;

