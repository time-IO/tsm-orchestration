DROP VIEW IF EXISTS foi_ts_coordinates CASCADE;
CREATE VIEW foi_ts_coordinates AS

WITH static_coords AS (
    SELECT
        FALSE AS is_dynamic,
        at.action_id,
        at.datastream_id,
        at.begin_date,
        at.result_time,
        at.c_label,
        CASE
            WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y, 0]
            ELSE ARRAY[sla.x, sla.y, sla.z]
        END AS coordinates,
        hashtextextended(CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, at.action_id, at.is_dynamic),0) AS feature_id
    FROM foi_ts_action_type at
    LEFT JOIN public.sms_configuration_static_location_begin_action sla
           ON sla.id = at.action_id
    WHERE at.is_dynamic = FALSE

),
-- for the dynamic things
--    assigning the three datastream_ids (x/y/z) for each main_datastream_id
xyzDatastream AS MATERIALIZED
    (
SELECT DISTINCT
    dma.configuration_id,
    dla.id as dla_id,
    dsl_main.datastream_id AS main_datastream_id,
    dsl_x.datastream_id AS x_datastream_id,
    dsl_y.datastream_id AS y_datastream_id,
    dsl_z.datastream_id AS z_datastream_id
FROM sms_configuration_dynamic_location_begin_action dla
JOIN sms_device_mount_action dma
    ON dma.configuration_id = dla.configuration_id
-- main_datastream
JOIN sms_datastream_link dsl_main
    ON dsl_main.device_mount_action_id = dma.id
    AND dsl_main.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
-- x_datastream_id
JOIN sms_datastream_link dsl_x
    ON dsl_x.device_mount_action_id = dma.id
    AND dsl_x.device_property_id = dla.x_property_id
-- y_datastream_id
JOIN sms_datastream_link dsl_y
    ON dsl_y.device_mount_action_id = dma.id
    AND dsl_y.device_property_id = dla.y_property_id
-- z_datastream_id
LEFT JOIN sms_datastream_link dsl_z
    ON dsl_z.device_mount_action_id = dma.id
    AND dsl_z.device_property_id = dla.z_property_id),

    dynamic_coords AS (
    SELECT
        TRUE AS is_dynamic,
        at.action_id::int,
        at.datastream_id,  -- original datastream!
        at.begin_date,
        at.result_time,
        at.c_label,
        CASE
            WHEN oz.result_number IS NULL THEN ARRAY[ox.result_number, oy.result_number]
            ELSE ARRAY[ox.result_number, oy.result_number, oz.result_number]
        END AS coordinates,
         hashtextextended(CONCAT(ARRAY[ox.result_number, oy.result_number, COALESCE(oz.result_number, 0)]::text, at.action_id, at.is_dynamic),0) AS feature_id
        FROM foi_ts_action_type at
    JOIN xyzDatastream data ON data.main_datastream_id = at.datastream_id
    JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation ox
        ON ox.datastream_id = data.x_datastream_id
        AND ox.result_time = at.result_time
    JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation oy
        ON oy.datastream_id = data.y_datastream_id
        AND oy.result_time = at.result_time
    LEFT JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation oz
        ON oz.datastream_id = data.z_datastream_id
        AND oz.result_time = at.result_time
  )
SELECT * FROM static_coords
UNION ALL
SELECT * FROM dynamic_coords;

