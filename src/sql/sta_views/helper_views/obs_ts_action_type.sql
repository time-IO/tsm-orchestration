-- -- Helper view ts_action_type determines the action type (static or dynamic)
-- -- and the action ID (ID from sms_configuration_static / dynamic_location_begin_action).
-- -- with arguments for the observation-View
--
-- -- BEGIN;
-- --
-- -- SET search_path TO %(tsm_schema)s;
--
-- DROP VIEW IF EXISTS obs_ts_action_type CASCADE;
-- CREATE OR REPLACE VIEW obs_ts_action_type AS
--
--
-- WITH configuration_type AS (
--   SELECT
--   dsl.datastream_id,
--         CASE
--             WHEN sla.id IS NOT NULL THEN FALSE
--             WHEN dla.id IS NOT NULL THEN TRUE
--             ELSE NULL
--         END AS is_dynamic,
--
--         CASE
--             WHEN sla.id IS NOT NULL THEN sla.id
--             WHEN dla.id IS NOT NULL THEN dla.id
--             ELSE NULL
--         END AS action_id,
--
--        CASE
--             WHEN sla.id IS NOT NULL THEN sla.begin_date
--             WHEN dla.id IS NOT NULL THEN dla.begin_date
--             ELSE NULL
--         END AS begin_date,
--
--         CASE
--             WHEN sla.id IS NOT NULL THEN sla.end_date
--             WHEN dla.id IS NOT NULL THEN dla.end_date
--             ELSE NULL
--         END AS end_date,
--
--         CASE
--             WHEN sla.id IS NOT NULL THEN sla.valid_range
--             WHEN dla.id IS NOT NULL THEN dla.valid_range
--             ELSE NULL
--         END AS valid_range
--
--       FROM sms_datastream_link dsl
--            JOIN sms_device_mount_action dma ON dsl.device_mount_action_id = dma.id
--            JOIN public.sms_device d ON d.id = dma.device_id
--            JOIN public.sms_configuration c ON c.id = dma.configuration_id
--          LEFT JOIN sms_configuration_static_location_begin_action_neu sla ON sla.configuration_id = c.id
--          LEFT JOIN sms_configuration_dynamic_location_begin_action_neu dla ON dla.configuration_id = c.id
-- --      WHERE c.is_public AND d.is_public AND dsl.datasource_id = 'vo_demogroup_887a7030491444e0aee126fbc215e9f7'
--   )
--
--
--
-- SELECT DISTINCT
--     o.id AS o_id,
--     o.datastream_id AS o_datastream_id,
--     o.result_time,
--     ct.is_dynamic,
--     ct.action_id,
--     ct.begin_date,
--     o.result_boolean,
--     o.result_quality,
--     o.result_string,
--     o.result_json,
--     o.result_number,
--     o.valid_time_start,
--     o.result_type,
--     o.valid_time_end
--
--
-- FROM vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o
--     LEFT JOIN configuration_type ct ON o.datastream_id = ct.datastream_id
--                                             AND  o.result_time <@ ct.valid_range
--     WHERE is_dynamic IS NOT NULL
--       AND action_id IS NOT NULL
--
-- ORDER BY o_id;
--
-- -- COMMIT;

DROP VIEW IF EXISTS obs_ts_action_type CASCADE;
CREATE OR REPLACE VIEW obs_ts_action_type AS

WITH action_ranges AS NOT MATERIALIZED (
    -- Static
    SELECT
        dsl.datastream_id,
        FALSE AS is_dynamic,
        sla.id AS action_id,
        sla.begin_date,
        sla.valid_range
    FROM sms_configuration_static_location_begin_action_neu sla
    JOIN public.sms_configuration c ON c.id = sla.configuration_id
    JOIN sms_device_mount_action dma ON dma.configuration_id = c.id
    JOIN public.sms_device d ON d.id = dma.device_id
    JOIN sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id

    UNION ALL

    -- Dynamic
    SELECT
        dsl.datastream_id,
        TRUE AS is_dynamic,
        dla.id AS action_id,
        dla.begin_date,
        dla.valid_range
    FROM sms_configuration_dynamic_location_begin_action_neu dla
    JOIN public.sms_configuration c ON c.id = dla.configuration_id
    JOIN sms_device_mount_action dma ON dma.configuration_id = c.id
    JOIN public.sms_device d ON d.id = dma.device_id
    JOIN sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
)
SELECT DISTINCT
    o.id AS o_id,
    o.datastream_id AS o_datastream_id,
    o.result_time,
    ar.is_dynamic,
    ar.action_id,
    ar.begin_date,
    o.result_boolean,
    o.result_quality,
    o.result_string,
    o.result_json,
    o.result_number,
    o.valid_time_start,
    o.result_type,
    o.valid_time_end
FROM vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o
JOIN action_ranges ar
    ON o.datastream_id = ar.datastream_id
    AND o.result_time <@ ar.valid_range
ORDER BY o_id;