DROP VIEW IF EXISTS obs_ts_coordinates_v2 CASCADE;
CREATE VIEW obs_ts_coordinates_v2 AS

WITH

static_coords AS (
    SELECT
        'static' AS action_type,
        aa.action_id,
        aa.datastream_id,
        aa.begin_date,
        aa.result_time,
        aa.o_id,
        aa.result_boolean,
        aa.result_quality,
        aa.result_string,
        aa.result_json,
        aa.result_number,
        aa.valid_time_start,
        aa.result_type,
        aa.valid_time_end,
        aa.device_property_id,
        CASE
            WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y]
            ELSE ARRAY[sla.x, sla.y, sla.z]
        END AS coordinates,
    hashtextextended(CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, aa.action_id, 'stat'),0) AS feature_id
--       ('x' || MD5(CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, aa.action_id, 'stat')))::bit(63)::bigint AS feature_id
    FROM obs_ts_action_type_v2 aa
    INNER JOIN sms_configuration_static_location_begin_action sla
        ON sla.id = aa.action_id
    WHERE aa.is_dynamic = FALSE
),

dynamic_coords AS (
    SELECT
        'dynamic' AS action_type,
        aa.action_id,
        aa.datastream_id,
        aa.begin_date,
        aa.result_time,
        aa.o_id,
        aa.result_boolean,
        aa.result_quality,
        aa.result_string,
        aa.result_json,
        aa.result_number,
        aa.valid_time_start,
        aa.result_type,
        aa.valid_time_end,
        aa.device_property_id,
        CASE
            WHEN z.z_koor IS NULL THEN ARRAY[x.x_koor, y.y_koor]
            ELSE ARRAY[x.x_koor, y.y_koor, z.z_koor]
        END AS coordinates,
           hashtextextended(CONCAT(ARRAY[x.x_koor, y.y_koor, COALESCE(z.z_koor, 0)]::text, aa.action_id, 'dyn'),0) AS feature_id
-- ('x' || MD5(CONCAT(ARRAY[x.x_koor, y.y_koor, COALESCE(z.z_koor, 0)]::text, aa.action_id, 'dyn')))::bit(63)::bigint AS feature_id
    FROM obs_ts_action_type_v2 aa
    INNER JOIN ts_coordinates_x_koor_test x
        ON x.result_time = aa.result_time
       AND x.datastream_id = aa.datastream_id
    INNER JOIN ts_coordinates_y_koor_test y
        ON y.result_time = aa.result_time
       AND y.datastream_id = aa.datastream_id
    LEFT JOIN ts_coordinates_z_koor_test z
        ON z.result_time = aa.result_time
       AND z.datastream_id = aa.datastream_id
    WHERE aa.is_dynamic = TRUE)


SELECT * FROM static_coords
UNION ALL
SELECT * FROM dynamic_coords
LIMIT 100;





