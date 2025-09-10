DROP VIEW IF EXISTS ts_action_type2 CASCADE;
CREATE OR REPLACE VIEW ts_action_type2 AS
WITH configuration_type AS (SELECT DISTINCT

                                dma.configuration_id,
                             dma.id AS ct_dma_id,
                                CASE
                                                WHEN sla.id IS NOT NULL THEN TRUE -- statische Location-Action
                                                WHEN dla.id IS NOT NULL THEN FALSE -- dynamische Location-Action
                                                ELSE NULL -- Ungültige Konfiguration
                                                END AS action_type,


                                            CASE
                                                WHEN sla.id IS NOT NULL THEN sla.id
                                                WHEN dla.id IS NOT NULL THEN dla.id
                                                ELSE NULL
                                                END AS action_id


                            FROM sms_device_mount_action dma

                                     LEFT JOIN sms_configuration_static_location_begin_action sla
                                               ON sla.configuration_id = dma.configuration_id
                                     LEFT JOIN sms_configuration_dynamic_location_begin_action dla
                                               ON dla.configuration_id = dma.configuration_id
--                                     JOIN sms_configuration c ON dma.configuration_id = c.id
                            )

SELECT    DISTINCT ON ( o.result_time, ct.action_type, o.datastream_id, ct.ct_dma_id)

  o.datastream_id,
    o.result_time,
--     o.id AS akt_observation_id,
    ct.action_type,
    ct.action_id,
 ct.ct_dma_id
-- ct.configuration_id
 FROM vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o
    JOIN sms_datastream_link dsl ON o.datastream_id = dsl.datastream_id
    JOIN device_mount_action dma ON dsl.device_mount_action_id = dma.id
    JOIN configuration_type ct ON dma.configuration_id = ct.configuration_id

;