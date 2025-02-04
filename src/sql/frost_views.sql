BEGIN;

--- CREATE VIEW "THINGS" ---
DROP VIEW IF EXISTS "THINGS" CASCADE;
CREATE OR REPLACE VIEW "THINGS" AS
SELECT DISTINCT c.id AS "ID",
       c.description AS "DESCRIPTION",
       c.label AS "NAME",
       jsonb_build_object(
               'url',  %(sms_url)s || 'configurations/' || c.id,
               'pid',  c.persistent_identifier,
               'status', c.status,
               'mobile', CASE
                   WHEN MAX(cdl.begin_date) IS NULL THEN 'false'
                   ELSE 'true'
               END,
               'organizations', ARRAY_AGG(DISTINCT co.organization),
               'projects', ARRAY_AGG(DISTINCT c.project),
               'when_dynamic', ARRAY_AGG(
                   DISTINCT CASE
                       WHEN cdl.end_date IS NULL THEN
                                                 TO_CHAR(cdl.begin_date,
                                                         'YYYY-MM-DD HH24:MI:SS TZ')
                       ELSE
                                                 TO_CHAR(cdl.begin_date,
                                                         'YYYY-MM-DD HH24:MI:SS TZ') ||
                                                 '/' ||
                                                 TO_CHAR(cdl.end_date, 'YYYY-MM-DD HH24:MI:SS TZ')
                   END
                   ),
               'when_stationary', ARRAY_AGG(
                   DISTINCT CASE
                       WHEN csl.end_date IS NULL THEN
                                                 TO_CHAR(csl.begin_date,
                                                         'YYYY-MM-DD HH24:MI:SS TZ')
                       ELSE
                                                 TO_CHAR(csl.begin_date,
                                                         'YYYY-MM-DD HH24:MI:SS TZ') ||
                                                 '/' ||
                                                 TO_CHAR(csl.end_date, 'YYYY-MM-DD HH24:MI:SS TZ')
                   END
                   ),
               'contacts', ARRAY_AGG(
                   DISTINCT jsonb_build_object(
                       'name', CONCAT(co.given_name, ' ', co.family_name),
                       'email', co.email,
                       'organization', co.organization,
                       'orcid', co.orcid
                   ))
           ) AS "PROPERTIES"
FROM public.sms_configuration c
         JOIN public.sms_configuration_contact_role ccr ON c.id = ccr.configuration_id
         JOIN public.sms_contact co ON ccr.contact_id = co.id
         JOIN public.sms_device_mount_action dma ON c.id = dma.configuration_id
         JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
         LEFT JOIN public.sms_configuration_dynamic_location_begin_action cdl
                   ON c.id = cdl.configuration_id
         LEFT JOIN public.sms_configuration_static_location_begin_action csl
                   ON c.id = csl.configuration_id
WHERE ((cdl.configuration_id IS NOT NULL) OR (csl.configuration_id IS NOT NULL))
  AND dsl.datasource_id = %(tsm_schema)s
  AND c.is_public
GROUP BY c.id, c.description, c.label, c.persistent_identifier, c.status, c.is_public,
    cdl.configuration_id, csl.configuration_id, dsl.datasource_id
ORDER BY c.id ASC;


--- CREATE VIEW SENSORS ---
DROP VIEW IF EXISTS "SENSORS" CASCADE;
CREATE OR REPLACE VIEW "SENSORS" AS
SELECT DISTINCT d.id                                                             AS "ID",
    d.short_name AS "NAME",
    d.description AS "DESCRIPTION",
    'html'::text AS "ENCODING_TYPE",
                %(sms_url)s || 'backend/api/v1/devices/' || d.id ||
                '/sensorml'                                                      AS "METADATA",
    jsonb_build_object(
      'url',  %(sms_url)s || 'devices/' || d.id,
        'pid', d.persistent_identifier,
        'type', d.device_type_name,
        'contacts', ARRAY_AGG(DISTINCT jsonb_build_object(
            'email', co.email,
            'organization', co.organization,
            'name', CONCAT(co.given_name, ' ', co.family_name),
            'orcid', co.orcid
        )),
        'manufacturer', d.manufacturer_name,
        'model', d.model,
        'serialNumber', d.serial_number
    ) AS "PROPERTIES"
FROM public.sms_device d
         JOIN public.sms_device_mount_action dma ON d.id = dma.device_id
         JOIN public.sms_configuration_contact_role ccr
              ON dma.configuration_id = ccr.configuration_id
         JOIN public.sms_contact co ON ccr.contact_id = co.id
         JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
 WHERE dsl.datasource_id = %(tsm_schema)s
  AND d.is_public
GROUP BY d.id, d.short_name, d.description, d.persistent_identifier, d.device_type_name,
    d.manufacturer_name, d.model, d.serial_number, d.is_public, dsl.datasource_id
ORDER BY d.id ASC;


--- CREATE VIEW LOCATIONS ---
DROP VIEW IF EXISTS "LOCATIONS" CASCADE;
CREATE OR REPLACE VIEW "LOCATIONS" AS
SELECT DISTINCT csl.id                       AS "ID",
    csl.label AS "NAME",
                csl.begin_description        AS "DESCRIPTION",
    'application/geo+json'::text AS "ENCODING_TYPE",
    public.ST_ASGeoJSON(
        public.ST_SetSRID(
            public.ST_MakePoint(csl.x, csl.y),
            4326
        )
    ) AS "LOCATION",
    jsonb_build_object() AS "PROPERTIES"
FROM public.sms_configuration_static_location_begin_action csl
         JOIN public.sms_configuration c ON csl.configuration_id = c.id
         JOIN public.sms_device_mount_action dma ON c.id = dma.configuration_id
         JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
 WHERE dsl.datasource_id = %(tsm_schema)s
  AND c.is_public
ORDER BY csl.id;


--- CREATE VIEW THINGS_LOCATIONS ---
DROP VIEW IF EXISTS "THINGS_LOCATIONS" CASCADE;
CREATE OR REPLACE VIEW "THINGS_LOCATIONS" AS
SELECT DISTINCT ON (c.id) c.id   AS "THING_ID",
    csl.id AS "LOCATION_ID"
FROM public.sms_configuration c
         JOIN public.sms_configuration_static_location_begin_action csl
              ON c.id = csl.configuration_id
         JOIN public.sms_device_mount_action dma ON c.id = dma.configuration_id
         JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
 WHERE dsl.datasource_id = %(tsm_schema)s
  AND c.is_public
ORDER BY c.id, csl.begin_date DESC;


--- CREATE VIEW LOCATIONS_HIST_LOCATIONS ---
DROP VIEW IF EXISTS "LOCATIONS_HIST_LOCATIONS" CASCADE;
CREATE OR REPLACE VIEW "LOCATIONS_HIST_LOCATIONS" AS
--build cte that returns configuration_ids and location_ids (configuration_static_location_begin_action.id)
WITH config_locations AS (SELECT DISTINCT c.id   AS c_id,
        csl.id AS csl_id
    FROM public.sms_configuration c
                                   JOIN public.sms_configuration_static_location_begin_action csl
                                        ON c.id = csl.configuration_id
                                   JOIN public.sms_device_mount_action dma
                                        on c.id = dma.configuration_id
                                   JOIN public.sms_datastream_link dsl
                                        on dma.id = dsl.device_mount_action_id
                           WHERE dsl.datasource_id = %(tsm_schema)s
                            AND c.is_public),
-- return newest location (highest csl_id) for each configuration_id
-- might need to be decided based on timestamp.
-- for now, taking the highest id works fine
     locations AS (SELECT c_id,
    MAX(csl_id) AS max_csl_id
  FROM config_locations
                   GROUP BY c_id)
-- join locations on newest locaiton per configuration id
SELECT loc.max_csl_id AS "LOCATION_ID",
    cl.csl_id AS "HIST_LOCATION_ID"
-- join locations on newest location on configuration id
FROM config_locations cl
         JOIN locations loc ON cl.c_id = loc.c_id
-- leave out newest location in join
WHERE cl.csl_id <> loc.max_csl_id
ORDER BY loc.max_csl_id ASC, cl.csl_id ASC
--returns hist_location_id for mapped to current location_id for each configuration_id
;


--- CREATE VIEW HIST_LOCATIONS ---
DROP VIEW IF EXISTS "HIST_LOCATIONS" CASCADE;
CREATE OR REPLACE VIEW "HIST_LOCATIONS" AS
WITH cte AS (SELECT c.id                                                  AS "THING_ID",
        csl.id "ID",
        csl.begin_date AS "TIME",
                    ROW_NUMBER()
                    OVER (PARTITION BY c.id ORDER BY csl.begin_date DESC) AS row_num
    FROM public.sms_configuration c
                      JOIN public.sms_configuration_static_location_begin_action csl
                           ON c.id = csl.configuration_id
             WHERE c.is_public)
SELECT DISTINCT "THING_ID",
    "ID",
    "TIME"
FROM cte
         JOIN public.sms_device_mount_action dma
              on cte."THING_ID" = dma.configuration_id
         JOIN public.sms_datastream_link dsl on dma.id = dsl.device_mount_action_id
WHERE row_num > 1
  AND dsl.datasource_id = %(tsm_schema)s;


--- CREATE VIEW FEATURE_OF_INTEREST ---

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'FEATURES' 
        AND table_schema = %(tsm_schema)s 
        AND table_type = 'BASE TABLE') 
    THEN EXECUTE 'DROP TABLE "FEATURES" CASCADE';
    ELSIF EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'FEATURES' 
        AND table_schema = %(tsm_schema)s
        AND table_type = 'VIEW'
        ) 
    THEN EXECUTE 'DROP VIEW "FEATURES" CASCADE';
    END IF;
END $$;
CREATE TABLE "FEATURES" (
  "ID" serial,
  "NAME" text,
  "DESCRIPTION" text,
  "ENCODING_TYPE" text,
  "FEATURE" jsonb,
  "PROPERTIES" jsonb
);

--- CREATE VIEW OBSERVATIONS ---
DROP VIEW IF EXISTS "OBSERVATIONS" CASCADE;
CREATE OR REPLACE VIEW "OBSERVATIONS" AS
SELECT
    o.result_boolean AS "RESULT_BOOLEAN",
    o.result_quality AS "RESULT_QUALITY",
    o.phenomenon_time_start AS "PHENOMENON_TIME_START",
    jsonb_build_object() AS "PARAMETERS",
    dsl.device_property_id AS "DATASTREAM_ID",
    o.result_string AS "RESULT_STRING",
    o.result_type AS "RESULT_TYPE",
    o.valid_time_end AS "VALID_TIME_END",
    o.phenomenon_time_end AS "PHENOMENON_TIME_END",
    null AS "FEATURE_ID",
    row_number() OVER () AS "ID",
    o.result_json AS "RESULT_JSON",
    o.result_time AS "RESULT_TIME",
    o.result_number AS "RESULT_NUMBER",
    o.valid_time_start AS "VALID_TIME_START"
FROM public.sms_datastream_link dsl
JOIN observation o ON o.datastream_id = dsl.datastream_id
JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
JOIN public.sms_device d ON d.id = dma.device_id
JOIN public.sms_configuration c ON c.id = dma.configuration_id
WHERE c.is_public AND d.is_public AND dsl.datasource_id = %(tsm_schema)s;


--- CREATE VIEW DATASTREAMS ---
DROP VIEW IF EXISTS "DATASTREAMS" CASCADE;
CREATE OR REPLACE VIEW "DATASTREAMS" AS SELECT
    dsl.device_property_id AS "ID",
    CONCAT(
        c.label, '_',
        d.short_name, '_',
        dp.property_name, '_',
        dma.offset_z, '_',
        dp.aggregation_type_name) AS "NAME",
    CONCAT(
        d.short_name, '_',
        dp.property_name, '_',
        dma.offset_z, ' at site ',
        c.label, ' with aggregation function ',
        dp.aggregation_type_name) AS "DESCRIPTION",
    c.id AS "THING_ID",
    d.id AS "SENSOR_ID",
    'OM_Observation' AS "OBSERVATION_TYPE",
    dma.begin_date AS "PHENOMENON_TIME_START",
    dma.begin_date AS "RESULT_TIME_START",
    dma.end_date AS "PHENOMENON_TIME_END",
    dma.end_date AS "RESULT_TIME_END",
    -- we don't provide an observed area, as this is really expensive
    null as "OBSERVED_AREA",
    dp.unit_uri AS "UNIT_DEFINITION",
    dp.property_name AS "UNIT_NAME",
    dp.unit_name AS "UNIT_SYMBOL",
    CASE
                    WHEN dp.property_uri = '' THEN NULL
                    ELSE reverse(split_part(reverse(dp.property_uri::text), '/'::text,
                                            2))::integer
    END as "OBS_PROPERTY_ID",
    jsonb_build_object(
		'sensorOutput', dp.property_name,
		'offset', jsonb_build_object(
			'z', dma.offset_z,
			'unit', 'm'),
		'aggregation', jsonb_build_object(
			'period', dsl.aggregation_period,
			'function', dp.aggregation_type_name),
		'quality', jsonb_build_object(
			'resolution', dp.resolution,
			'resolution_unit', dp.resolution_unit_name,
			'accuracy', dp.accuracy,
			'measuring_range_min', dp.measuring_range_min,
			'measuring_range_max', dp.measuring_range_max),
                        'license', '')            AS "PROPERTIES"

FROM public.sms_datastream_link dsl
    JOIN public.sms_device_mount_action dma ON dma.id = dsl.device_mount_action_id
    JOIN public.sms_device d ON d.id = dma.device_id
    JOIN public.sms_configuration c ON c.id = dma.configuration_id
    JOIN public.sms_device_property dp ON dp.id = dsl.device_property_id
WHERE dsl.datasource_id = %(tsm_schema)s AND c.is_public AND d.is_public;

--- CREATE VIEW OBS_PROPERTIES ---
DROP VIEW IF EXISTS "OBS_PROPERTIES" CASCADE;
CREATE OR REPLACE VIEW "OBS_PROPERTIES" AS
SELECT DISTINCT mq.id         as  "ID",
    mq.term as "NAME",
    mq.provenance_uri "DEFINITION",
    mq.definition as "DESCRIPTION",
                jsonb_build_object('url', %(cv_url)s  || 'api/v1/measuredquantities/' || mq.id)
        as "PROPERTIES"
FROM public.sms_cv_measured_quantity mq
         JOIN public.sms_device_property dp
              ON mq.id = reverse(split_part(reverse(dp.property_uri), '/', 2))::int
         JOIN public.sms_device_mount_action dma ON dp.device_id = dma.device_id
         JOIN public.sms_configuration c ON dma.configuration_id = c.id
         JOIN public.sms_device d ON dma.device_id = d.id
         JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
         LEFT JOIN public.sms_configuration_static_location_begin_action csl
                   on dma.configuration_id = csl.configuration_id
         LEFT JOIN public.sms_configuration_dynamic_location_begin_action cdl
                   on dma.configuration_id = cdl.configuration_id
WHERE (cdl.configuration_id IS NOT NULL OR csl.configuration_id IS NOT NULL)
  AND c.is_public
  AND d.is_public
  AND dp.property_uri <> ''
  AND dsl.datasource_id =  %(tsm_schema)s;

COMMIT;
