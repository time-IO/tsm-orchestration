DROP VIEW IF EXISTS ts_coordinates_cases CASCADE;
CREATE OR REPLACE VIEW ts_coordinates_cases AS
EXPLAIN ANALYZE
WITH

aktionen AS (
    SELECT
        ts.result_time,
        ts.action_type,
        ts.action_id::int,  -- sla/dla id
        ts.datastream_id,
        dma.configuration_id,
        dma.id AS stat_dma_id -- dma_id nur für static, nicht für dyn. -> hier falsche Ausgabe (JOIN ... ON sla.configuration_id)

    FROM ts_action_type ts
    JOIN sms_configuration_static_location_begin_action sla ON sla.id = ts.action_id
    JOIN sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id -- wird hier nur eingebunden, um an die dma für static zu kommen
    WHERE ts.action_id = dma.id -- daher hier

),

static_coords AS (
    SELECT DISTINCT
        'static' AS action_type,
        a.action_id,
        a.datastream_id,
        sla.id::int AS stat_sla_id, -- 🛠️ explizit casten
        a.stat_dma_id AS stat_dma_id,
        NULL::integer AS dyn_dma_id,

        CASE
            WHEN   sla.z IS NULL THEN ARRAY[sla.x, sla.y]
            ELSE ARRAY[sla.x, sla.y, sla.z]
        END AS coordinates
--         a.result_time,

    FROM aktionen a
    LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = a.configuration_id AND sla.id = a.action_id
    JOIN sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
    WHERE a.action_type = TRUE AND a.action_id =a.stat_dma_id
),

dynamic_coords AS (
    SELECT
        'dynamic' AS action_type,

        a.datastream_id,
        a.stat_dma_id AS stat_dma_id,
         x.dyn_dma_id,
        a.action_id::int AS action_id, -- 🛠️ sicherheitshalber auch hier



        CASE
            WHEN z.z_koor IS NULL THEN ARRAY[x.x_koor, y.y_koor]
            ELSE ARRAY[x.x_koor, y.y_koor, z.z_koor]
        END AS coordinates
      --  a.result_time
    FROM aktionen a
    LEFT JOIN ts_coordinates_x_koor x ON x.result_time = a.result_time
    LEFT JOIN ts_coordinates_y_koor y ON y.result_time = a.result_time
    LEFT JOIN ts_coordinates_z_koor z ON z.result_time = a.result_time
    WHERE a.action_type = FALSE
)

SELECT
        action_type,
        action_id,
       datastream_id,
       dyn_dma_id,
       stat_dma_id,
       coordinates
FROM static_coords

UNION ALL

SELECT action_type,
       action_id,
       datastream_id,
       dyn_dma_id,
       stat_dma_id,
       coordinates
FROM dynamic_coords;

