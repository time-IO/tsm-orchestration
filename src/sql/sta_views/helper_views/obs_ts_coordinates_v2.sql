DROP VIEW IF EXISTS obs_ts_coordinates_v2 CASCADE;
CREATE VIEW obs_ts_coordinates_v2 AS

WITH

static_coords AS (
    SELECT
        'static' AS action_type,
        at.action_id,
        at.datastream_id,
        at.begin_date,
        at.result_time,
        at.o_id,
        at.result_boolean,
        at.result_quality,
        at.result_string,
        at.result_json,
        at.result_number,
        at.valid_time_start,
        at.result_type,
        at.valid_time_end,
        at.device_property_id,
        CASE
            WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y]
            ELSE ARRAY[sla.x, sla.y, sla.z]
        END AS coordinates,
    hashtextextended(CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, at.action_id, 'stat'),0) AS feature_id
    FROM obs_ts_action_type_v2 at
    INNER JOIN sms_configuration_static_location_begin_action sla
        ON sla.id = at.action_id
    WHERE at.is_dynamic = FALSE
),

dynamic_coords AS (
    SELECT
        'dynamic' AS action_type,
        at.action_id,
        at.datastream_id,
        at.begin_date,
        at.result_time,
        at.o_id,
        at.result_boolean,
        at.result_quality,
        at.result_string,
        at.result_json,
        at.result_number,
        at.valid_time_start,
        at.result_type,
        at.valid_time_end,
        at.device_property_id,
        CASE
            WHEN z.z_koor IS NULL THEN ARRAY[x.x_koor, y.y_koor]
            ELSE ARRAY[x.x_koor, y.y_koor, z.z_koor]
        END AS coordinates,
           hashtextextended(CONCAT(ARRAY[x.x_koor, y.y_koor, COALESCE(z.z_koor, 0)]::text, at.action_id, 'dyn'),0) AS feature_id
    FROM obs_ts_action_type_v2 at
    INNER JOIN ts_coordinates_x_koor_test x
        ON x.result_time = at.result_time
       AND x.datastream_id = at.datastream_id
    INNER JOIN ts_coordinates_y_koor_test y
        ON y.result_time = at.result_time
       AND y.datastream_id = at.datastream_id
    LEFT JOIN ts_coordinates_z_koor_test z
        ON z.result_time = at.result_time
       AND z.datastream_id = at.datastream_id
    WHERE at.is_dynamic = TRUE)


SELECT * FROM static_coords
UNION ALL
SELECT * FROM dynamic_coords;





