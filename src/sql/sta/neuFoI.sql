DROP VIEW IF EXISTS "FEATURES2" CASCADE;
CREATE OR REPLACE VIEW "FEATURES2" AS

-- EXPLAIN ANALYZE
SELECT DISTINCT ON ("ID") -- beschränkter Distinkt, um Dopplungen bei den static zu umgehen (dma und sla.id)

   ('x' || MD5(crd.coordinates::text || crd.action_id))::bit(63)::bigint AS "ID",
                -- Zusammenbau der FoI_id: Hash aus Koordinaten und action_id
                -- (muss berechenbar sein, damit sie auch unabhängig dem observation_table zur Verfügung steht)
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
	jsonb_build_object()  AS "PROPERTIES"



FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
JOIN public.sms_configuration c ON c.id =dma.configuration_id
JOIN public.sms_device d ON d.id = dma.device_id
JOIN ts_coordinates_cases crd ON crd.datastream_id = dsl.datastream_id
    WHERE dma.id = crd.stat_dma_id OR dma.id = crd.dyn_dma_id
GROUP BY crd.action_type, crd.coordinates, crd.action_id, c."label", dsl.begin_date;

