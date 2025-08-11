BEGIN;

DROP VIEW IF EXISTS "location_property_order" CASCADE;
CREATE OR REPLACE VIEW "location_property_order" AS
SELECT DISTINCT
	dsl.device_property_id,
	CASE
		WHEN dsl.device_property_id =dla.x_property_id THEN 1
		WHEN dsl.device_property_id =dla.y_property_id THEN 2
		WHEN dsl.device_property_id =dla.z_property_id THEN 3
	END	AS "location_property_order"
FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id=dsl.device_mount_action_id
JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id =dma.configuration_id
JOIN public.sms_configuration c ON c.id = dma.configuration_id
JOIN public.sms_device d ON d.id = dma.device_id
WHERE dsl.datasource_id = %(tsm_schema)s AND c.is_public AND d.is_public;

COMMIT;