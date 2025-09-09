DROP VIEW IF EXISTS ts_coordinates_cases CASCADE;
CREATE OR REPLACE VIEW ts_coordinates_cases AS
--     View zur Bestimmung der Koordinaten, Unterscheidung der static/dynamic actions,
--     später durch UNION wieder zusammengefügt, daher gleicher Aufbau (columns)

WITH

static_coords AS (SELECT DISTINCT ON (sla.id) -- beschränkter Distinct, da bei static ein FoI für eine sla.id
                      'static'      AS action_type,
                       at.action_id,
                       at.datastream_id,
                       dma.id        AS stat_dma_id,
                       NULL::integer AS dyn_dma_id, -- Leerstelle für dyn_dma_id

                         CASE
                            WHEN sla.z IS NULL THEN ARRAY [sla.x, sla.y]
                            ELSE ARRAY [sla.x, sla.y, sla.z]
                         END       AS coordinates

                  FROM ts_action_type at
                           LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.id = at.action_id
                           JOIN sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
                  WHERE at.action_type = TRUE),


-- CTE um die Koordinaten der dynamic actions zu bestimmten (WHERE at.action_type = FALSE),
    -- Zugriff auf die einzelnen Helper-Views für die x/y/z- Koordinaten, über result-time
dynamic_coords AS (SELECT 'dynamic'     AS action_type,
                          at.action_id::int,
                          at.datastream_id,
                          NULL::integer AS stat_dma_id, --Leerstelle für stat_dma_id
                          x.dyn_dma_id,
                          CASE
                              WHEN z.z_koor IS NULL THEN ARRAY [x.x_koor, y.y_koor]
                              ELSE ARRAY [x.x_koor, y.y_koor, z.z_koor]
                              END       AS coordinates

                   FROM ts_action_type at
                            LEFT JOIN ts_coordinates_x_koor x ON x.result_time = at.result_time
                            LEFT JOIN ts_coordinates_y_koor y ON y.result_time = at.result_time
                            LEFT JOIN ts_coordinates_z_koor z ON z.result_time = at.result_time
                   WHERE at.action_type = FALSE
                    AND at.datastream_id IN (x.datastream_id, y.datastream_id, z.datastream_id)
    )


SELECT action_type,
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

