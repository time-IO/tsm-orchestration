
CREATE OR REPLACE VIEW foi_features_combined AS

SELECT
    feature_id, is_dynamic, action_id, label, begin_date, coordinates
FROM (
    SELECT DISTINCT ON (sla.id)
        hashtextextended(CONCAT(ARRAY[sla.x, sla.y, COALESCE(sla.z, 0)]::text, sla.id, FALSE), 0) AS feature_id,
        FALSE AS is_dynamic,
        sla.id AS action_id,
        c.label,
        sla.begin_date,
        CASE WHEN sla.z IS NULL THEN ARRAY[sla.x, sla.y, 0] ELSE ARRAY[sla.x, sla.y, sla.z] END AS coordinates
    FROM public.sms_configuration_static_location_begin_action sla
        JOIN public.sms_device_mount_action dma ON dma.configuration_id = sla.configuration_id
        JOIN public.sms_configuration c ON c.id = dma.configuration_id AND c.is_public
        JOIN public.sms_device d ON d.id = dma.device_id AND d.is_public
        JOIN public.sms_datastream_link dsl ON dsl.device_mount_action_id = dma.id
            AND dsl.datasource_id = '{tsm_schema}'
) static_coords


UNION ALL


SELECT
    feature_id, is_dynamic, action_id, label, begin_date, coordinates
FROM foi_catalog_dynamic