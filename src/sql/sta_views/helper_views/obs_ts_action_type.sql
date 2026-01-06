 DROP VIEW IF EXISTS obs_ts_action_type CASCADE;
CREATE OR REPLACE VIEW obs_ts_action_type AS


WITH

static_action AS (
    SELECT
        o.id AS o_id,
        FALSE AS is_dynamic,
        o.datastream_id,
        o.result_time,
        o.result_boolean,
        o.result_quality,
        o.result_string,
        o.result_json,
        o.result_number,
        o.valid_time_start,
        o.result_type,
        o.valid_time_end,
        sla.id AS action_id,
        sla.begin_date,
        dsl.device_property_id,
        c.label,
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
--         AND dsl.datasource_id = 'crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b'
       AND dsl.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
--     JOIN crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b.observation o
            JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation o
        ON o.datastream_id = dsl.datastream_id
      WHERE o.result_time >= sla.begin_date
        AND o.result_time <= COALESCE(sla.end_date, 'infinity'::timestamp)
--         AND o.result_time BETWEEN dsl.begin_date AND COALESCE(dsl.end_date, 'infinity'::timestamp)

),
dynamic_action AS (
    SELECT
        o.id AS o_id,
        TRUE AS is_dynamic,
        o.datastream_id,
        o.result_time,
        o.result_boolean,
        o.result_quality,
        o.result_string,
        o.result_json,
        o.result_number,
        o.valid_time_start,
        o.result_type,
        o.valid_time_end,
        dla.id AS action_id,
        dla.begin_date,
        dsl.device_property_id,
        c.label,
        dma.configuration_id
    FROM public.sms_configuration_dynamic_location_begin_action dla
    JOIN public.sms_device_mount_action dma
        ON dma.configuration_id = dla.configuration_id
    JOIN public.sms_configuration c
        ON c.id = dma.configuration_id AND c.is_public
    JOIN public.sms_device d ON d.id = dma.device_id AND d.is_public
    JOIN public.sms_datastream_link dsl
        ON dsl.device_mount_action_id = dma.id
       --         AND dsl.datasource_id = 'crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b'
       AND dsl.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
--     JOIN crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b.observation o
            JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation o
        ON o.datastream_id = dsl.datastream_id
--     WHERE  o.result_time BETWEEN dsl.begin_date
--           AND COALESCE(dsl.end_date, 'infinity'::timestamp)
--       AND

)
SELECT * FROM static_action
UNION ALL
SELECT * FROM dynamic_action;
