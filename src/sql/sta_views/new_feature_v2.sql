DROP VIEW IF EXISTS "NEW_FEATURES" CASCADE;
CREATE VIEW "NEW_FEATURES" AS


SELECT DISTINCT
    crd.feature_id AS "ID",
 	CONCAT(crd.c_label, '_', crd.begin_date) AS "NAME",
 	    CASE
 	        WHEN crd.is_dynamic IS FALSE THEN 'static'
 	            ELSE 'dynamic'
 	        END AS "DESCRIPTION",
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
JOIN foi_ts_action_type_coord crd ON crd.datastream_id = dsl.datastream_id
;

