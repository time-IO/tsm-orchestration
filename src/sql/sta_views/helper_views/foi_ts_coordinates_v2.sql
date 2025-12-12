
DROP VIEW IF EXISTS foi_ts_coordinates_v2 CASCADE;
CREATE VIEW foi_ts_coordinates_v2 AS

WITH



static_coords AS (
    SELECT
        'static' AS action_type,
        ba.action_id,
        ba.datastream_id,
        ba.begin_date,
        ba.result_time,
        ba.c_label,
        CASE
            WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y, 0]
            ELSE ARRAY[sla.x, sla.y, sla.z]
        END AS coordinates
    FROM foi_ts_action_type_v2 ba
    LEFT JOIN public.sms_configuration_static_location_begin_action sla
           ON sla.id = ba.action_id
    WHERE ba.is_dynamic = FALSE
),

dynamic_coords AS (
    SELECT
        'dynamic' AS action_type,
        ba.action_id::int,
        ba.datastream_id,
        ba.begin_date,
        ba.result_time,
        ba.c_label,
        CASE
            WHEN z.z_koor IS NULL THEN ARRAY[x.x_koor, y.y_koor]
            ELSE ARRAY[x.x_koor, y.y_koor, z.z_koor]
        END AS coordinates
    FROM foi_ts_action_type_v2 ba
    LEFT JOIN ts_coordinates_x_koor x
           ON x.result_time = ba.result_time
    LEFT JOIN ts_coordinates_y_koor y
           ON y.result_time = ba.result_time
    LEFT JOIN ts_coordinates_z_koor z
           ON z.result_time = ba.result_time
    WHERE ba.is_dynamic = TRUE
      AND ba.datastream_id IN (x.datastream_id, y.datastream_id, z.datastream_id)
)

SELECT action_type, action_id, datastream_id, begin_date, result_time, c_label, coordinates,
       CONCAT(coordinates, action_id, 'stat') AS feature_id
FROM static_coords

UNION ALL

SELECT action_type, action_id, datastream_id, begin_date, result_time, c_label, coordinates,
       CONCAT(coordinates, action_id, 'dyn') AS feature_id
FROM dynamic_coords;







