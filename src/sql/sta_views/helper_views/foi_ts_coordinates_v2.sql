-- View for determining the coordinates, distinguishing between static/dynamic actions,
-- later merged again using UNION, therefore the same structure (columns).
-- BEGIN;
--
-- SET search_path TO %(tsm_schema)s;

DROP VIEW IF EXISTS foi_ts_coordinates_v2 CASCADE;
CREATE OR REPLACE VIEW foi_ts_coordinates_v2 AS


WITH

static_coords AS (SELECT  DISTINCT ON (action_id)
                      'static'      AS action_type,
                       at.action_id,
                       at.datastream_id,
                       at.begin_date,
                       at.result_time,
                       at.c_label,
                         CASE
                            WHEN sla.z IS NULL THEN ARRAY [sla.x, sla.y]
                            ELSE ARRAY [sla.x, sla.y, sla.z]
                         END AS coordinates


                  FROM foi_ts_action_type_v2 at
                           LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.id = at.action_id
                  WHERE at.is_dynamic = FALSE),


dynamic_coords AS (SELECT
                    'dynamic'     AS action_type,
                     at.action_id::int,
                     at.datastream_id,
                     at.begin_date,
                     at.result_time,
                     at.c_label,
                        CASE
                          WHEN z.z_koor IS NULL THEN ARRAY [x.x_koor, y.y_koor]
                          ELSE ARRAY [x.x_koor, y.y_koor, z.z_koor]
                        END AS coordinates

                   FROM foi_ts_action_type_v2 at
                            LEFT JOIN ts_coordinates_x_koor x ON x.result_time = at.result_time
                            LEFT JOIN ts_coordinates_y_koor y ON y.result_time = at.result_time
                            LEFT JOIN ts_coordinates_z_koor z ON z.result_time = at.result_time
                   WHERE at.is_dynamic = TRUE
                    AND at.datastream_id IN (x.datastream_id, y.datastream_id, z.datastream_id)
    )


SELECT action_type,
       action_id,
       datastream_id,
       begin_date,
       result_time,
       c_label,
       coordinates,
        CONCAT(coordinates, action_id, 'stat') AS feature_id
FROM static_coords

UNION ALL

SELECT action_type,
       action_id,
       datastream_id,
       begin_date,
       result_time,
       c_label,
       coordinates,
       CONCAT(coordinates, action_id, 'dyn') AS feature_id
FROM dynamic_coords;

-- COMMIT;