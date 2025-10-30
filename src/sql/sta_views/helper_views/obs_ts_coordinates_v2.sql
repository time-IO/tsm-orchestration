-- View for determining the coordinates, distinguishing between static/dynamic actions,
-- later merged again using UNION, therefore the same structure (columns).

DROP VIEW IF EXISTS obs_ts_coordinates_v2 CASCADE;
CREATE OR REPLACE VIEW obs_ts_coordinates_v2 AS


WITH static_coords AS (SELECT
                      'static'      AS action_type,
                       at.action_id,
                       at.datastream_id,
                       at.begin_date,
                       at.result_time,
                       at.id,
                       at.result_boolean,
                       at.result_quality,
                       at.result_string,
                       at.result_json,
                       at.result_number,
                       at.valid_time_start,
                       at.result_type,
                       at.valid_time_end,
                      CASE
                            WHEN sla.z IS NULL THEN ARRAY [sla.x, sla.y]
                            ELSE ARRAY [sla.x, sla.y, sla.z]
                         END AS coordinates

                  FROM obs_ts_action_type_v2 at
                    LEFT JOIN public.sms_configuration_static_location_begin_action sla ON sla.id = at.action_id
                        WHERE at.is_dynamic = FALSE),


dynamic_coords AS (SELECT
                    'dynamic'     AS action_type,
                     at.action_id::int,
                     at.datastream_id,
                     at.begin_date,
                     at.result_time,
                     at.id,
                     at.result_boolean,
                     at.result_quality,
                     at.result_string,
                     at.result_json,
                     at.result_number,
                     at.valid_time_start,
                     at.result_type,
                     at.valid_time_end,
                     CASE WHEN x.x_koor IS NOT NULL AND y.y_koor IS NOT NULL THEN
                       CASE
                          WHEN z.z_koor IS NULL THEN ARRAY [x.x_koor, y.y_koor]
                          ELSE ARRAY [x.x_koor, y.y_koor, z.z_koor]
                        END
                        ELSE NULL
                        END AS coordinates

                   FROM obs_ts_action_type_v2 at
                            LEFT JOIN ts_coordinates_x_koor x ON x.result_time = at.result_time
                            LEFT JOIN ts_coordinates_y_koor y ON y.result_time = at.result_time
                            LEFT JOIN ts_coordinates_z_koor z ON z.result_time = at.result_time
                   WHERE at.is_dynamic = TRUE
    )


SELECT
       id AS o_id,
       action_type,
       action_id,
       datastream_id AS o_datastream_id,
       begin_date,
       result_time,
       result_boolean,
       result_quality,
       result_string,
       result_json,
       result_number,
       valid_time_start,
       result_type,
       valid_time_end,
       coordinates,
       CONCAT(coordinates, action_id, 'stat') AS feature_id
    FROM static_coords

UNION ALL

SELECT

       id AS o_id,
       action_type,
       action_id,
       datastream_id AS o_datastream_id,
       begin_date,
       result_time,
       result_boolean,
       result_quality,
       result_string,
       result_json,
       result_number,
       valid_time_start,
        result_type,
       valid_time_end,
       coordinates,
       CONCAT(coordinates, action_id, 'dyn') AS feature_id
    FROM dynamic_coords;







