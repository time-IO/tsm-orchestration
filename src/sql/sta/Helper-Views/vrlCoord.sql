--
-- DROP VIEW IF EXISTS test_coordinates_dyn  CASCADE;
-- CREATE OR REPLACE VIEW test_coordinates AS
--
--
--
-- WITH xkoordinaten AS
--     (SELECT
-- dla.x_property_id,
-- dsl.datastream_id,
-- o.result_time as x_result_time,
-- o.result_number as xko
-- FROM public.sms_datastream_link dsl
--     LEFT JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
-- JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
-- LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
-- WHERE (dsl.device_property_id = dla.x_property_id)
--  )
-- SELECT DISTINCT
--
-- xkoordinaten.x_result_time,
-- o.result_time,
-- xkoordinaten.x_property_id,
-- xkoordinaten.xko,
-- dla.y_property_id,
-- o.result_number
-- FROM public.sms_datastream_link dsl
--     LEFT JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
--     LEFT JOIN xkoordinaten ON xkoordinaten.x_result_time= o.result_time
-- JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
-- LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
-- WHERE (dsl.device_property_id = dla.y_property_id);
--
--

-- von mir ohne chatgpt (halber Datensatz??!)
DROP VIEW IF EXISTS test_coordinates_Hanna  CASCADE;
CREATE OR REPLACE VIEW test_coordinates_Hanna AS
WITH xkoordinaten AS
    (SELECT
dla.x_property_id,
dsl.datastream_id,
o.result_time as x_result_time,
o.result_number as xko
FROM public.sms_datastream_link dsl
    LEFT JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
WHERE (dsl.device_property_id = dla.x_property_id)
 )
SELECT DISTINCT
ts_action.action_type,
CASE
    WHEN ts_action.action_type = 'static' THEN
	        CASE
				WHEN sla.z IS NULL THEN array[sla.x ,sla.y]
				ELSE array[sla.x ,sla.y, sla.z]
			END
    WHEN ts_action.action_type = 'dynamic' THEN
                array[xko, o.result_number]
END as Koordinaten,
xkoordinaten.x_result_time,
o.result_time
-- xkoordinaten.x_property_id,
-- xkoordinaten.xko,
-- dla.y_property_id,
-- o.result_number


FROM public.sms_datastream_link dsl
    LEFT JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
    JOIN v2_ts_action_type ts_action ON ts_action.result_time  = o.result_time
   LEFT JOIN xkoordinaten ON xkoordinaten.x_result_time= o.result_time

JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = dma.configuration_id
WHERE (dsl.device_property_id = dla.y_property_id OR sla.id=ts_action.action_id);

DROP VIEW IF EXISTS test_coordinates CASCADE;
CREATE OR REPLACE VIEW test_coordinates AS

WITH
-- Dynamische X-Koordinate
xkoordinaten AS (
    SELECT
        o.result_time,
        o.result_number AS xko
    FROM sms_datastream_link dsl
    JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
    JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
    JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
    WHERE dsl.device_property_id = dla.x_property_id
),

-- Dynamische Y-Koordinate
ykoordinaten AS (
    SELECT
        o.result_time,
        o.result_number AS yko
    FROM sms_datastream_link dsl
    JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
    JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
    JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
    WHERE dsl.device_property_id = dla.y_property_id
),

-- Dynamische Z-Koordinate
zkoordinaten AS (
    SELECT
        o.result_time,
        o.result_number AS zko
    FROM sms_datastream_link dsl
    JOIN sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
    JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
    JOIN  vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
    WHERE dsl.device_property_id = dla.z_property_id
),

-- Aktionen mit Typ und zugehöriger Konfiguration
aktionen AS (
    SELECT
        ts.result_time,
        ts.action_type,
        ts.action_id,
        dma.configuration_id
    FROM v2_ts_action_type ts
    JOIN sms_configuration_static_location_begin_action sla ON sla.id = ts.action_id
    JOIN sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
)

SELECT DISTINCT
    a.action_type,
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
    END AS koordinaten,
    a.result_time
FROM aktionen a
LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = a.configuration_id
LEFT JOIN xkoordinaten x ON x.result_time = a.result_time
LEFT JOIN ykoordinaten y ON y.result_time = a.result_time
LEFT JOIN zkoordinaten z ON z.result_time = a.result_time;