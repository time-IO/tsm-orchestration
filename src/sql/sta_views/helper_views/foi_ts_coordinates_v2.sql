
DROP VIEW IF EXISTS foi_ts_coordinates_v2 CASCADE;
CREATE VIEW foi_ts_coordinates_v2 AS

WITH
-- Zuerst: Materialisiere die Basis-View einmalig
base_actions AS MATERIALIZED (
    SELECT
        action_id,
        datastream_id,
        begin_date,
        result_time,
        c_label,
        is_dynamic
    FROM foi_ts_action_type_v2
),

static_coords AS MATERIALIZED (
    SELECT
        'static' AS action_type,
        ba.action_id,
        ba.datastream_id,
        ba.begin_date,
        ba.result_time,
        ba.c_label,
        CASE
            WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y]
            ELSE ARRAY[sla.x, sla.y, sla.z]
        END AS coordinates,
         hashtextextended(CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, ba.action_id, 'stat'),0) AS feature_id
    FROM base_actions ba
    LEFT JOIN public.sms_configuration_static_location_begin_action sla
           ON sla.id = ba.action_id
    WHERE ba.is_dynamic = FALSE
),

dynamic_coords AS MATERIALIZED (
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
        END AS coordinates,
        hashtextextended(CONCAT(ARRAY[x.x_koor, y.y_koor, COALESCE(z.z_koor, 0)]::text, ba.action_id, 'dyn'),0) AS feature_id
    FROM base_actions ba
    LEFT JOIN ts_coordinates_x_koor_test x
           ON x.result_time = ba.result_time
    LEFT JOIN ts_coordinates_y_koor_test y
           ON y.result_time = ba.result_time
    LEFT JOIN ts_coordinates_z_koor_test z
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






