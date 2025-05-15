DROP VIEW IF EXISTS "SENSORS" CASCADE;
CREATE VIEW "SENSORS" AS
WITH
    device_role_responsible_persons AS (
        SELECT DISTINCT
        d.id AS "device_id",
        dcr.role_name AS "role_name",
        dcr.role_uri AS "role_uri",
        array_agg(DISTINCT jsonb_build_object(
            'jsonld.id', '{sms_url}' || 'contacts/' || co.id,
            'jsonld.type', 'Person',
            'givenName', co.given_name,
            'familyName', co.family_name,
            'email', co.email,
            'affiliation', jsonb_build_object(
                'jsonld.type', 'Organization',
                'name', co.organization,
                'identifier', NULL
            ),
            'identifier', co.orcid
        )) AS "responsible_persons"
        FROM public.sms_device d
        JOIN public.sms_device_contact_role dcr ON dcr.device_id = d.id
        JOIN public.sms_contact co ON dcr.contact_id = co.id
        GROUP BY d.id, dcr.role_name, dcr.role_uri),

    device_properties AS (
        SELECT DISTINCT
        d.id AS "device_id",
        jsonb_build_object(
            '@context', public.get_schema_org_context(),
            'jsonld.id', '{sms_url}' || 'devices/' || d.id,
            'jsonld.type', 'SensorProperties',
            'identifier', d.persistent_identifier,
            'isVariantOf', jsonb_build_object(
                'jsonld.type', 'ProductGroup',
                'name', d.device_type_name,
                'definition', d.device_type_uri
            ),
            'isVirtual', false,
            'model', d.model,
            'manufacturer', jsonb_build_object(
                'jsonld.type', 'Organization',
                'name', d.manufacturer_name,
                'definition', d.manufacturer_uri
            ),
            'serialNumber', d.serial_number,
            'responsiblePersons', array_agg(DISTINCT jsonb_build_object(
                'jsonld.type', 'Person',
                'roleName', drrp.role_name,
                'definition', drrp.role_uri,
                'resonsiblePersons', drrp.responsible_persons
            ))
        ) AS "properties"
    FROM public.sms_device d
    JOIN device_role_responsible_persons drrp ON d.id = drrp.device_id
    JOIN public.sms_device_mount_action dma ON d.id = dma.device_id
    JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
    JOIN public.sms_configuration c ON dma.configuration_id = c.id
    LEFT JOIN public.sms_configuration_dynamic_location_begin_action cdl ON c.id = cdl.configuration_id
    LEFT JOIN public.sms_configuration_static_location_begin_action csl ON c.id = csl.configuration_id
    GROUP BY d.id, d.persistent_identifier, d.device_type_name, d.device_type_uri, d.model,
        d.manufacturer_name, d.manufacturer_uri, d.serial_number, c.is_public, d.is_public,
        cdl.configuration_id, csl.configuration_id, dsl.datasource_id
    HAVING ((cdl.configuration_id IS NOT NULL) OR (csl.configuration_id IS NOT NULL))
        AND d.is_public
        AND c.is_public
        AND dsl.datasource_id = '{tsm_schema}')
SELECT
    d.id AS "ID",
    d.short_name AS "NAME",
    d.description AS "DESCRIPTION",
    'html' AS "ENCODING_TYPE",
    '{sms_url}' || 'backend/api/v1/devices/' || d.id || '/sensorml' AS "METADATA",
    dp.properties AS "PROPERTIES"
FROM public.sms_device d
JOIN device_properties dp ON d.id = dp.device_id
ORDER BY d.id ASC;
