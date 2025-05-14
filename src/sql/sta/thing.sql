BEGIN;

SET search_path TO '{tsm_schema}';

DROP VIEW IF EXISTS "THINGS" CASCADE;
CREATE OR REPLACE VIEW "THINGS" AS
WITH
    configuration_role_responsible_persons AS (
    SELECT
        c.id AS "configuration_id",
        ccr.role_name AS "role_name",
        ccr.role_uri AS "role_uri",
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
            )
        ) AS "responsible_persons"
    FROM public.sms_configuration c
    JOIN public.sms_configuration_contact_role ccr ON c.id = ccr.configuration_id
    JOIN public.sms_contact co ON ccr.contact_id = co.id
    GROUP BY c.id, ccr.role_name, ccr.role_uri
    ),
    configuration_properties AS (
    SELECT
    c.id AS "configuration_id",
    jsonb_build_object(
        '@context', public.get_schema_org_context(),
        'jsonld.id', '{sms_url}' || 'configurations/' || c.id,
        'jsonld.type', 'ThingProperties',
        'identifier', c.persistent_identifier,
        'responsiblePersons', array_agg(DISTINCT jsonb_build_object(
            'jsonld.type', 'Role',
            'roleName', crrp.role_name,
            'definition', crrp.role_uri,
            'resonsiblePersons', crrp.responsible_persons
        )),
        'partOfProjects', array_agg(DISTINCT jsonb_build_object(
            'jsonld.type', 'Project',
            'name', c.project
        )),
        'metadata', jsonb_build_object('jsonld.type', 'Dataset',
            'encodingType', 'http://www.opengis.net/doc/IS/SensorML/2.0',
            'distribution', jsonb_build_object(
                'jsonld.type', 'DataDistributionService',
                'url', '{sms_url}' || 'cbackend/api/v1/configurations/' || c.id || '/sensorml'
            )
        ),
    'isVirtual', false
    ) AS "properties"
    FROM public.sms_configuration c
    JOIN public.sms_configuration_contact_role ccr ON c.id = ccr.configuration_id
    JOIN public.sms_contact co ON ccr.contact_id = co.id
    JOIN public.sms_device_mount_action dma ON c.id = dma.configuration_id
    JOIN public.sms_device d ON dma.device_id = d.id
    JOIN public.sms_datastream_link dsl ON dma.id = dsl.device_mount_action_id
    JOIN configuration_role_responsible_persons crrp ON c.id = crrp.configuration_id
    LEFT JOIN public.sms_configuration_dynamic_location_begin_action cdl ON c.id = cdl.configuration_id
    LEFT JOIN public.sms_configuration_static_location_begin_action csl ON c.id = csl.configuration_id
    GROUP BY
    c.id, c.persistent_identifier, c.project, cdl.configuration_id, csl.configuration_id,
    c.is_public, d.is_public, dsl.datasource_id
    HAVING
    ((cdl.configuration_id IS NOT NULL) OR (csl.configuration_id IS NOT NULL))
    AND c.is_public AND d.is_public AND dsl.datasource_id = '{tsm_schema}'
    )
SELECT DISTINCT
    c.id AS "ID",
    c.description AS "DESCRIPTION",
    c.label AS "NAME",
    cp.properties AS "PROPERTIES"
FROM public.sms_configuration c
JOIN configuration_properties cp ON c.id = cp.configuration_id
ORDER BY c.id ASC;

COMMIT;