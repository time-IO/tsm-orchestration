DROP VIEW IF EXISTS "LOCATIONS" CASCADE;
DROP VIEW IF EXISTS "THINGS_LOCATIONS" CASCADE;
DROP VIEW IF EXISTS "LOCATIONS_HIST_LOCATIONS" CASCADE;
DROP VIEW IF EXISTS "HIST_LOCATIONS" CASCADE;

CREATE VIEW "LOCATIONS" AS
SELECT DISTINCT
    csl.id AS "ID",
    csl.label AS "NAME",
    csl.begin_description AS "DESCRIPTION",
    'application/geo+json'::text AS "ENCODING_TYPE",
    public.ST_ASGeoJSON(
        public.ST_SetSRID(
            public.ST_MakePoint(csl.x, csl.y),
            4326)) AS "LOCATION",
    jsonb_build_object(
        '@context', public.get_schema_org_context(),
        'jsonld.id', '{sms_url}' || 'configurations/' || c.id || 'locations/static-location-actions/' || csl.id,
        'jsonld.type', 'LocationProperties') AS "PROPERTIES"
FROM public.sms_configuration_static_location_begin_action csl
JOIN public.sms_configuration c ON csl.configuration_id = c.id
JOIN public.sms_device_mount_action dma ON c.id = dma.configuration_id
JOIN public.sms_device d ON dma.device_id = d.id
JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
WHERE dsl.datasource_id = '{tsm_schema}'
  AND c.is_public
  AND d.is_public
ORDER BY csl.id;


--- CREATE VIEW THINGS_LOCATIONS ---
CREATE VIEW "THINGS_LOCATIONS" AS
SELECT DISTINCT ON (c.id)
    c.id   AS "THING_ID",
    csl.id AS "LOCATION_ID"
FROM public.sms_configuration c
JOIN public.sms_configuration_static_location_begin_action csl ON c.id = csl.configuration_id
JOIN public.sms_device_mount_action dma ON c.id = dma.configuration_id
JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
JOIN public.sms_device d ON dma.device_id = d.id
WHERE dsl.datasource_id = '{tsm_schema}'
  AND c.is_public
  AND d.is_public
ORDER BY c.id, csl.begin_date DESC;


CREATE VIEW "LOCATIONS_HIST_LOCATIONS" AS
--build cte that returns configuration_ids and location_ids (configuration_static_location_begin_action.id)
WITH locations AS (
        SELECT DISTINCT c.id AS c_id, csl.id AS csl_id
        FROM public.sms_configuration c
        JOIN public.sms_configuration_static_location_begin_action csl ON c.id = csl.configuration_id
        JOIN public.sms_device_mount_action dma on c.id = dma.configuration_id
        JOIN public.sms_device d ON dma.device_id = d.id
        JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
        WHERE dsl.datasource_id = '{tsm_schema}'
        AND c.is_public AND d.is_public),
    current_locations AS (
        SELECT c_id, MAX(csl_id) AS max_csl_id
        FROM locations
        GROUP BY c_id)
SELECT
    cl.max_csl_id AS "LOCATION_ID",
    loc.csl_id AS "HIST_LOCATION_ID"
FROM locations loc
-- join locations on current configuration location
JOIN current_locations cl ON loc.c_id = cl.c_id
ORDER BY cl.max_csl_id ASC, loc.csl_id ASC
--returns hist_location_id mapped to current location_id for each configuration_id
;

CREATE VIEW "HIST_LOCATIONS" AS
WITH cte AS (
    SELECT c.id AS "THING_ID", csl.id "ID", csl.begin_date AS "TIME",
    ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY csl.begin_date DESC) AS row_num
    FROM public.sms_configuration c
    JOIN public.sms_configuration_static_location_begin_action csl ON c.id = csl.configuration_id
    JOIN public.sms_device_mount_action dma ON c.id = dma.configuration_id
    JOIN public.sms_device d ON dma.device_id = d.id
    JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
    WHERE c.is_public
      AND d.is_public
      AND dsl.datasource_id = '{tsm_schema}')
SELECT DISTINCT
    "THING_ID",
    "ID",
    "TIME"
FROM cte
WHERE row_num > 1;
