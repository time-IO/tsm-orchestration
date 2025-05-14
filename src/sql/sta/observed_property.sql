BEGIN;

SET search_path TO '{tsm_schema}';

DROP VIEW IF EXISTS "OBS_PROPERTIES" CASCADE;
CREATE OR REPLACE VIEW "OBS_PROPERTIES" AS
SELECT DISTINCT
    mq.id as "ID",
    mq.term as "NAME",
    mq.provenance_uri "DEFINITION",
    mq.definition as "DESCRIPTION",
    jsonb_build_object(
        '@context', public.get_schema_org_context(),
        'jsonld.id', '{cv_url}' || 'api/v1/measuredquantities/' || mq.id,
        'jsonld.type', 'ObservedPropertyProperties'
    ) as "PROPERTIES"
FROM public.sms_cv_measured_quantity mq
JOIN public.sms_device_property dp ON mq.id = reverse(split_part(reverse(dp.property_uri), '/', 2))::int
JOIN public.sms_device_mount_action dma ON dp.device_id = dma.device_id
JOIN public.sms_configuration c ON dma.configuration_id = c.id
JOIN public.sms_device d ON dma.device_id = d.id
JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
LEFT JOIN public.sms_configuration_static_location_begin_action csl ON dma.configuration_id = csl.configuration_id
LEFT JOIN public.sms_configuration_dynamic_location_begin_action cdl ON dma.configuration_id = cdl.configuration_id
WHERE (cdl.configuration_id IS NOT NULL OR csl.configuration_id IS NOT NULL)
    AND c.is_public AND d.is_public AND dp.property_uri <> '' AND dsl.datasource_id = '{tsm_schema}';

COMMIT;