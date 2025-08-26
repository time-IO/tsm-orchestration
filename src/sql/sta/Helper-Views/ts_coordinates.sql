--         DROP VIEW IF EXISTS ts_coordinates CASCADE;
--         CREATE OR REPLACE VIEW ts_coordinates  AS
--
--         WITH
--         -- Dynamische X-Koordinate
--         xkoordinaten AS (
--             SELECT
--                 o.result_time,
--                 o.result_number AS xko,
--                 dla.x_property_id,
--                 dma.id AS dyn_dma_id,
--                 dsl.datastream_id
--             FROM sms_datastream_link dsl
--             JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
--             JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
--             JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
--             WHERE dsl.device_property_id = dla.x_property_id
--         ),
--
--         -- Dynamische Y-Koordinate
--         ykoordinaten AS (
--             SELECT
--                 o.result_time,
--                 o.result_number AS yko,
--                 dsl.datastream_id AS y_datastream,
--             dla.y_property_id
--             FROM sms_datastream_link dsl
--             JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
--             JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
--             JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
--             WHERE dsl.device_property_id = dla.y_property_id
--         ),
--
--         -- Dynamische Z-Koordinate
--         zkoordinaten AS (
--             SELECT
--                 o.result_time,
--                 o.result_number AS zko
--             FROM sms_datastream_link dsl
--             JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
--             JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
--             JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
--             WHERE dsl.device_property_id = dla.z_property_id
--         ),
--
--         -- Aktionen mit Typ und zugehöriger Konfiguration
--         aktionen AS (
--             SELECT
--                 ts.result_time,
--                 ts.action_type,
--                 ts.action_id,
--                 dma.configuration_id,
--                 dma.id AS akt_dma_id,
-- --                 ts.observation_id,
--                 ts.datastream_id
--             FROM ts_action_type ts
--             JOIN sms_configuration_static_location_begin_action sla ON sla.id = ts.action_id
--             JOIN sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
--         )
--
--         SELECT DISTINCT
--             a.action_type,
--             CASE
--                 WHEN a.action_type = 'static' THEN
--                     CASE
--                         WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y]
--                         ELSE ARRAY[sla.x, sla.y, sla.z]
--                     END
--                 WHEN a.action_type = 'dynamic' THEN
--                     CASE
--                         WHEN z.zko IS NULL THEN ARRAY[x.xko, y.yko]
--                         ELSE ARRAY[x.xko, y.yko, z.zko]
--                     END
--             END AS coordinates,
--             a.result_time,
--             a.action_id,
-- --             a.observation_id,
--             a.datastream_id,
-- --             a.akt_dma_id,
--            x.dyn_dma_id,
-- --             sla.id AS sla_action_id,
-- --             x.device_property_id,
--           x.x_property_id as x_Prop,
--           x.datastream_id as x_Datastream,
--           y.y_property_id,
--             y.y_datastream
--         FROM aktionen a
--         LEFT JOIN xkoordinaten x ON x.result_time = a.result_time
--         LEFT JOIN ykoordinaten y ON y.result_time = a.result_time
--         LEFT JOIN zkoordinaten z ON z.result_time = a.result_time
--           LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = a.configuration_id AND sla.id = a.action_id
--             WHERE a.action_id = a.akt_dma_id;
--
-- -- EXPLAIN ANALYZE  SELECT * FROM v2_ts_action_type
-- --                               test_coordinates
-- --                               vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation



-- Helper_view "ts_coordinates" ermittelt die Koordinaten aufgeschlüsselt nach static oder dynamic

DROP VIEW IF EXISTS ts_coordinates CASCADE;
        CREATE OR REPLACE VIEW ts_coordinates  AS
-- Da dür die dynamische Location die x-, y- und z-Koordinate in einzelnen Observations gespeichert werden,
-- wird für jede Koordinate eine eigene CTE für die Abfrage der betreffenden Observation gestartet.
-- Die Abfrage läuft über sms_datastream_link gebunden an die device_mount_action_id, die configuration_id und die datastream_id

        WITH
        -- CTE für dynamische x-Koordinate
        xkoordinaten AS (
            SELECT
                o.result_time,
                o.result_number AS xko, -- unter result_number werden die Koordinaten bereitgehalten
                dma.id AS dyn_dma_id --  device_mount_action_id für dynamic, da hier an dla gebunden
            FROM sms_datastream_link dsl
            JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
            JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
            JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
            -- Bedingung für x-Koordinate
            WHERE dsl.device_property_id = dla.x_property_id
        ),

        -- CTE für dynamische y-Koordinate
        ykoordinaten AS (
            SELECT
                o.result_time,
                o.result_number AS yko,
                --dsl.datastream_id AS y_datastream,
                dla.y_property_id
            FROM sms_datastream_link dsl
            JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
            JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
            JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
            -- Bedingung für y-Koordinate
            WHERE dsl.device_property_id = dla.y_property_id
        ),

        -- CTE für dynamische Z-Koordinate
        zkoordinaten AS (
            SELECT
                o.result_time,
                o.result_number AS zko
            FROM sms_datastream_link dsl
            JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
            JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
            JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
            WHERE dsl.device_property_id = dla.z_property_id
            -- Bedingung für z-Koordinate
        ),


        -- CTE Abfrage der Helper-View ts_action_type, inkl. Bestimmung der dma_id für static
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
                WHEN a.action_type = 'static' THEN
                    CASE
                        WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y]
                        ELSE ARRAY[sla.x, sla.y, sla.z]
                    END
                WHEN a.action_type = 'dynamic' THEN
                    CASE
                        WHEN z.zko IS NULL THEN ARRAY[x.xko, y.yko]
                        ELSE ARRAY[x.xko, y.yko, z.zko]
                    END
            END AS coordinates

        FROM aktionen a
        LEFT JOIN xkoordinaten x ON x.result_time = a.result_time
        LEFT JOIN ykoordinaten y ON y.result_time = a.result_time
        LEFT JOIN zkoordinaten z ON z.result_time = a.result_time
            -- damit keine Dopplung der Daten, müssen sowohl die sla_id als auch die dma_id aus 'aktionen' mit der action_id aus 'aktionen'
            -- übereinstimmen (letztere steht für die sla_id bei Überprüfung des Types)
          LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = a.configuration_id AND sla.id = a.action_id
            WHERE a.action_id = a.stat_dma_id
