DROP VIEW IF EXISTS foi_ts_action_type_coord CASCADE;
CREATE OR REPLACE VIEW foi_ts_action_type_coord AS

WITH
xyzDatastream AS MATERIALIZED (
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
        AND dsl_z.device_property_id = dla.z_property_id
),

static_distinct AS
    (
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
            AND o.result_time <= COALESCE(sla.end_date, 'infinity'::timestamp)),

    static_data AS
        (
 SELECT
        FALSE AS is_dynamic,
        sd.action_id,
        sd.datastream_id,
        sd.begin_date,
        sd.result_time,
        sd.c_label,
        CASE
            WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y, 0]
            ELSE ARRAY[sla.x, sla.y, sla.z]
        END AS coordinates,
        hashtextextended(CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, sd.action_id, sd.is_dynamic),0) AS feature_id
    FROM static_distinct sd
    LEFT JOIN public.sms_configuration_static_location_begin_action sla
           ON sla.id = sd.action_id
    WHERE sd.is_dynamic = FALSE),

    dynamic_data AS
        (
SELECT
    TRUE AS is_dynamic,
    dla.id AS action_id,
    o.datastream_id,
    dla.begin_date,
    o.result_time,
    c.label AS c_label,
    CASE
        WHEN oz.result_number IS NULL
        THEN ARRAY[ox.result_number, oy.result_number, 0]
        ELSE ARRAY[ox.result_number, oy.result_number, oz.result_number]
    END AS coordinates,
    hashtextextended(
        CONCAT(
            ARRAY[ox.result_number, oy.result_number, COALESCE(oz.result_number, 0)]::text,
            dla.id,
            TRUE
        ),
        0
    ) AS feature_id
FROM sms_configuration_dynamic_location_begin_action dla
JOIN sms_device_mount_action dma
    ON dma.configuration_id = dla.configuration_id
JOIN sms_configuration c
    ON c.id = dma.configuration_id
    AND c.is_public
JOIN sms_device d
    ON d.id = dma.device_id
    AND d.is_public
JOIN sms_datastream_link dsl
    ON dsl.device_mount_action_id = dma.id
    AND dsl.datasource_id = 'ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2'
JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation o
    ON o.datastream_id = dsl.datastream_id
JOIN xyzDatastream data
    ON data.main_datastream_id = o.datastream_id
JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation ox
    ON ox.datastream_id = data.x_datastream_id
    AND ox.result_time = o.result_time
JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation oy
    ON oy.datastream_id = data.y_datastream_id
    AND oy.result_time = o.result_time
LEFT JOIN ufztimese_aiamoartificial_4bf3ba9d58a34330bcda9c90471866e2.observation oz
    ON oz.datastream_id = data.z_datastream_id
    AND oz.result_time = o.result_time)

SELECT * FROM static_data

UNION ALL

SELECT * FROM dynamic_data



;