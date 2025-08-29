DROP VIEW IF EXISTS ts_coordinates_helper CASCADE;
CREATE OR REPLACE VIEW ts_coordinates_helper  AS

--  EXPLAIN ANALYZE

WITH
    aktionen AS (
            SELECT
                ts.result_time,
                ts.action_type,
                ts.action_id, -- sla/oder dla.id
--                 ts.observation_id,
                ts.datastream_id,
                dma.configuration_id,
                dma.id AS stat_dma_id -- dma_id nur für static, nicht für dyn. -> hier falsche Ausgabe (JOIN ... ON sla.id = ts.action_id)
            FROM ts_action_type ts
            JOIN sms_configuration_static_location_begin_action sla ON sla.id = ts.action_id
            JOIN sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
        )






        -- Hauptabfrage, Koordinatenabfrage über CTEs
        SELECT DISTINCT
            a.action_type,
            a.action_id,
            a.datastream_id,
            x.dyn_dma_id,
            sla.id,
            a.stat_dma_id,

            CASE
                WHEN a.action_type = TRUE THEN
                    CASE
                        WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y]
                        ELSE ARRAY[sla.x, sla.y, sla.z]
                    END
                WHEN a.action_type = FALSE THEN
                    CASE
                        WHEN z.z_koor IS NULL THEN ARRAY[x.x_koor, y.y_koor]
                        ELSE ARRAY[x.x_koor, y.y_koor, z.z_koor]
                    END
            END AS coordinates

        FROM aktionen a
        LEFT JOIN ts_coordinates_x_koor x ON x.result_time = a.result_time
        LEFT JOIN ts_coordinates_y_koor y ON y.result_time = a.result_time
        LEFT JOIN ts_coordinates_z_koor z ON z.result_time = a.result_time
            -- damit keine Dopplung der Daten, müssen sowohl die sla_id als auch die dma_id aus 'aktionen' mit der action_id aus 'aktionen'
            -- übereinstimmen (letztere steht für die sla_id bei Überprüfung des Types)
          LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = a.configuration_id AND sla.id = a.action_id
            WHERE a.action_id = a.stat_dma_id
