DROP VIEW IF EXISTS "DATASTREAMS" CASCADE;
CREATE VIEW "DATASTREAMS" AS
SELECT
    dsl.device_property_id AS "ID",
    concat(c.label, ':',
        d.short_name, ':',
        dp.property_name, ':',
        dp.label
    ) as "NAME",
    concat(d.short_name, ' ',
		dp.property_name, ' ',
		dma.offset_z, 'm at site ',
		c.label, ' with aggregation function ',
		dp.aggregation_type_name, ' and period ',
		dsl.aggregation_period , 's'
	) as "DESCRIPTION",
    c.id as "THING_ID",
    d.id as "SENSOR_ID",
    CASE
                    WHEN dp.property_uri = '' THEN NULL
                    ELSE reverse(split_part(reverse(dp.property_uri::text), '/'::text,
                                            2))::integer
    END as "OBS_PROPERTY_ID",
    dp.unit_uri AS "UNIT_DEFINITION",
    dp.property_name AS "UNIT_NAME",
    dp.unit_name AS "UNIT_SYMBOL",
	'OM_Observation' as "OBSERVATION_TYPE",
	jsonb_build_object(
	    'name', '',
		'symbol', dp.unit_name,
		'definition', dp.unit_uri
	) as "UNIT_OF_MEASUREMENT",
    public.ST_GeomFromText('POLYGON EMPTY') as "OBSERVED_AREA",
	null as "RESULT_TIME",
	null as "PHENOMENON_TIME",
	dma.begin_date AS "PHENOMENON_TIME_START",
    dma.begin_date AS "RESULT_TIME_START",
    dma.end_date AS "PHENOMENON_TIME_END",
    dma.end_date AS "RESULT_TIME_END",
	jsonb_build_object(
        '@context', public.get_schema_org_context(),
		'jsonld.id',  '{sms_url}' || 'datastream-links/' || MAX(dsl.id),
		'jsonld.type', 'DatastreamProperties',
		'observingProcedure', jsonb_build_object(
			'jsonld.type', 'ObservingProcedure',
			'name', dp.aggregation_type_name,
			'description', cv_agg.definition,
			'definition', dp.aggregation_type_uri,
			'properties', jsonb_build_object(
			    'period', dsl.aggregation_period,
			    'unitOfPeriod', jsonb_build_object(
			        'jsonld.type', 'Unit',
		            'name', cv_u.provenance,
					'symbol', cv_u.term,
					'definition', dp.unit_uri
				)
			)
		),
		'measurementProperties', jsonb_build_object(
	        'jsonld.type', 'MeasurementProperties',
            'measurementResolution', dp.resolution ,
			'unitOfMeasurementResolution', jsonb_build_object(
				'jsonld.type', 'Unit',
				'name', cv_ur.provenance,
				'symbol', dp.resolution_unit_name,
				'definition', dp.resolution_unit_uri
			),
		    'measurementAccuracy', dp.accuracy,
		    'unitOfMeasurementAccuracy', jsonb_build_object(
			    'jsonld.type', 'Unit',
			    'name', cv_ua.provenance,
			    'symbol', dp.accuracy_unit_name ,
			    'definition', dp.accuracy_unit_uri
		    ),
            'operationRange', array[dp.measuring_range_min,dp.measuring_range_max],
            'unitOfOperationRange', jsonb_build_object(
                'jsonld.type', 'Unit',
                'name', cv_ua.provenance,
                'symbol', dp.accuracy_unit_name ,
                'definition', dp.accuracy_unit_uri
            )
        ),
		'license', jsonb_build_object(
			'jsonld.type', 'CreativeWork',
    		'name', cv_l.term,
		    'url', cv_l.provenance_uri,
		    'provider', cv_l.definition
		),
		'providerMobility', CASE WHEN MAX(cdl.begin_date) IS NULL THEN 'static' ELSE 'dynamic' end,
		'deployment', jsonb_build_object(
			'jsonld.id', '{sms_url}' || 'configurations/' || c.id || '/platforms-and-devices?deviceMountAction=' || dma.id,
			'jsonld.type', 'Deployment',
			'name', dma."label",
			'description', dma.begin_description,
			'deploymentTime', dma.begin_date,
			'properties', jsonb_build_object(
				'jsonld.type', 'DeploymentProperties',
				'offsets', jsonb_build_object(
					'jsonld.type', 'Offset',
					'x', dma.offset_x,
					'y', dma.offset_y,
					'z', dma.offset_z
				),
			    'unitOfOffsets', jsonb_build_object(
				    'jsonld.type', 'Unit',
				    'name', 'meters',
				    'symbol', 'm',
	                -- this should be generated automatically. we need to find the unit id for meter
				    'definition', 'https://sms-cv.helmholtz.cloud/sms/cv/api/v1/units/63'
			    )
		    )
		),
		'dataSource', ''
	) as "PROPERTIES"
FROM public.sms_datastream_link dsl
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
JOIN public.sms_device d ON d.id = dma.device_id
JOIN public.sms_configuration c ON c.id = dma.configuration_id
JOIN public.sms_device_property dp ON dp.id = dsl.device_property_id
LEFT JOIN public.sms_cv_aggregation_type cv_agg ON coalesce(nullif(split_part(dp.aggregation_type_uri,'/',9),'')::integer) =cv_agg.id
LEFT JOIN public.sms_cv_unit cv_u  ON coalesce(nullif(split_part(dp.unit_uri ,'/',9),'')::integer) =cv_u.id
LEFT JOIN public.sms_cv_unit cv_ur ON coalesce(nullif(split_part(dp.resolution_unit_uri ,'/',9),'')::integer) =cv_ur.id
LEFT JOIN public.sms_cv_unit cv_ua ON coalesce(nullif(split_part(dp.accuracy_unit_uri ,'/',9),'')::integer) =cv_ua.id
LEFT JOIN public.sms_cv_license cv_l ON coalesce(nullif(split_part(dsl.license_uri,'/',9),'')::integer) =cv_l.id
LEFT JOIN public.sms_configuration_dynamic_location_begin_action cdl ON c.id = cdl.configuration_id
LEFT JOIN public.sms_configuration_static_location_begin_action csl ON c.id = csl.configuration_id
WHERE c.is_public AND d.is_public AND dsl.datasource_id = '{tsm_schema}'
GROUP BY dsl.device_property_id, c.label, d.short_name, dp.property_name, dma.offset_z, dp.aggregation_type_name, dsl.aggregation_period,
	dp.unit_name, dp.unit_uri, d.id, dp.id, cv_agg.definition, dp.aggregation_type_uri, cv_u.provenance, cv_u.term, dp.resolution, cv_ur.provenance,
	dp.resolution_unit_name, dp.resolution_unit_uri, dp.accuracy, cv_ua.provenance, dp.accuracy_unit_name, dp.accuracy_unit_uri, dp.measuring_range_min,
	dp.measuring_range_max, cv_l.term, cv_l.provenance_uri, cv_l.definition, c.id, dma.id, dma.label, dma.begin_description, dma.begin_date, dma.offset_x,
	dma.offset_y, csl.x, csl.y, dp.property_uri, dma.end_date, dp.label;