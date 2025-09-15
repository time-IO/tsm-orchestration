--     View zur Bestimmung der Koordinaten, Unterscheidung der static/dynamic actions,
--     später durch UNION wieder zusammengefügt, daher gleicher Aufbau (columns)


DROP VIEW IF EXISTS obs_ts_coordinates CASCADE;
CREATE OR REPLACE VIEW obs_ts_coordinates AS


WITH

static_coords AS (SELECT
--     DISTINCT ON (action_id)
                      'static'      AS action_type,
                       at.action_id,
                       at.o_datastream_id,
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
                      CASE
                            WHEN sla.z IS NULL THEN ARRAY [sla.x, sla.y]
                            ELSE ARRAY [sla.x, sla.y, sla.z]
                         END AS coordinates

                  FROM obs_ts_action_type at
                           LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.id = at.action_id
                  WHERE at.is_dynamic = FALSE),


dynamic_coords AS (SELECT
                    'dynamic'     AS action_type,
                     at.action_id::int,
                     at.o_datastream_id,
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
                     CASE WHEN x.x_koor IS NOT NULL AND y.y_koor IS NOT NULL THEN
                       CASE
                          WHEN z.z_koor IS NULL THEN ARRAY [x.x_koor, y.y_koor]
                          ELSE ARRAY [x.x_koor, y.y_koor, z.z_koor]
                        END
                        ELSE NULL
                        END AS coordinates

                   FROM obs_ts_action_type at
                            LEFT JOIN ts_coordinates_x_koor x ON x.result_time = at.result_time
                            LEFT JOIN ts_coordinates_y_koor y ON y.result_time = at.result_time
                            LEFT JOIN ts_coordinates_z_koor z ON z.result_time = at.result_time
                   WHERE at.is_dynamic = TRUE


--                      AND at.o_datastream_id IN (x.datastream_id, y.datastream_id, z.datastream_id)
    )


SELECT
       o_id,
       action_type,
       action_id,
       o_datastream_id,
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
       coordinates
FROM static_coords

UNION ALL

SELECT

       o_id,
       action_type,
       action_id,
       o_datastream_id,
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
       coordinates
FROM dynamic_coords;

