
DROP VIEW IF EXISTS "FEATURES" CASCADE;
CREATE OR REPLACE VIEW "FEATURES" AS
 EXPLAIN ANALYZE
SELECT
   ('x' || MD5(crd.coordinates::text || crd.action_id))::bit(63)::bigint AS "ID",
 	CONCAT(c.label, '_', dsl.begin_date) AS "NAME",
	crd.action_type AS "DESCRIPTION",
'application/geo+json' AS "ENCODING_TYPE",
	jsonb_build_object(
		'type', 'Feature',
		'geometry', jsonb_build_object(
			'type', 'Polygon',
			'coordinates',jsonb_build_array(crd.coordinates)
			)
		) AS "FEATURE",
	jsonb_build_object()  AS "PROPERTIES",

crd.action_id AS crd_action_id,
-- crd.akt_dma_id AS crd_akt_dma_id,
--crd.dyn_dma_id AS crd_dyn_dma_id,
dma.id AS foi_dma




FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
-- LEFT JOIN public.sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = dma.configuration_id
-- LEFT JOIN public.sms_configuration_static_location_begin_action sla ON sla.configuration_id = dma.configuration_id
JOIN public.sms_configuration c ON c.id =dma.configuration_id
JOIN public.sms_device d ON d.id = dma.device_id
--JOIN vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o ON o.datastream_id = dsl.datastream_id
JOIN v2_ts_coordinates crd ON crd.datastream_id = dsl.datastream_id --AND crd.akt_dma_id = crd.action_id
    WHERE dma.id = crd.action_id  OR dma.id = crd.dyn_dma_id

--WHERE crd.action_type = 'static'
--WHERE dsl.datasource_id = 'vo_demogroup_887a7030491444e0aee126fbc215e9f7' -- AND c.is_public AND d.is_public
GROUP BY crd.action_type, crd.coordinates, crd.action_id, c."label", dsl.begin_date, dma.id, crd.dyn_dma_id;
