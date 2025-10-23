DROP VIEW IF EXISTS obs_ts_action_type_v2 CASCADE;
CREATE OR REPLACE VIEW obs_ts_action_type_v2 AS

WITH static_action AS (
    SELECT
        o.*,
        sla.id AS action_id,
        sla.begin_date,
        FALSE AS is_dynamic
    FROM sms_configuration_static_location_begin_action_neu sla
    JOIN sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
    JOIN sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
    JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
    WHERE o.result_time <@ sla.valid_range
),
dynamic_action AS (
    SELECT
        o.*,
        dla.id AS action_id,
        dla.begin_date,
        TRUE AS is_dynamic
    FROM sms_configuration_dynamic_location_begin_action_neu dla
    JOIN sms_device_mount_action dma ON dma.configuration_id = dla.configuration_id
    JOIN sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
    JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
)
SELECT DISTINCT * FROM static_action
UNION ALL
SELECT * FROM dynamic_action;
