DROP VIEW IF EXISTS crns_test.obs_ts_action_type_coord CASCADE;
CREATE OR REPLACE VIEW crns_test.obs_ts_action_type_coord AS

WITH static_data AS (
    SELECT
        o.id AS o_id,
        o.result_boolean,
        o.result_quality,
        o.result_string,
        o.result_json,
        o.result_number,
        o.valid_time_start,
        o.result_type,
        o.valid_time_end,
        o.result_time,
        dsl.device_property_id,
        hashtextextended(
            CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, sla.id, FALSE), 0
        ) AS feature_id
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
      AND (sla.end_date IS NULL OR o.result_time <= sla.end_date)
      AND o.result_time >= dsl.begin_date
      AND (dsl.end_date IS NULL OR o.result_time <= dsl.end_date)
),

dynamic_data AS (
    SELECT
        o.id AS o_id,
        o.result_boolean,
        o.result_quality,
        o.result_string,
        o.result_json,
        o.result_number,
        o.valid_time_start,
        o.result_type,
        o.valid_time_end,
        o.result_time,
        dsl.device_property_id,
        fol.feature_id
    FROM crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b.foi_observation_lookup fol
        JOIN crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b.observation o
            ON o.id = fol.o_id
        JOIN public.sms_datastream_link dsl
            ON dsl.datastream_id = o.datastream_id
            AND dsl.datasource_id = 'crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b'
            AND o.result_time >= dsl.begin_date
            AND (dsl.end_date IS NULL OR o.result_time <= dsl.end_date)
)

SELECT * FROM static_data
UNION ALL
SELECT * FROM dynamic_data;