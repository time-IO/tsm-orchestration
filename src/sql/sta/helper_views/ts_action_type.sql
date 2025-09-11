
-- Helper-View "ts_action_type" ermittelt den Action-Type (static or dynamic)
-- und die Action-ID (ID von sms_configuration_static/dynamic_location_begin_action)

DROP VIEW IF EXISTS ts_action_type CASCADE;
CREATE OR REPLACE VIEW ts_action_type AS


WITH configuration_type AS (
  SELECT
    c.id AS configuration_id,
        CASE
            WHEN sla.id IS NOT NULL THEN FALSE
            WHEN dla.id IS NOT NULL THEN TRUE
            ELSE NULL
        END AS is_dynamic,

        CASE
            WHEN sla.id IS NOT NULL THEN sla.begin_date
            WHEN dla.id IS NOT NULL THEN dla.begin_date
        END AS begin_date,

        CASE
            WHEN sla.id IS NOT NULL THEN sla.id
            WHEN dla.id IS NOT NULL THEN dla.id
            ELSE NULL
        END AS action_id,

      CASE
                WHEN sla.id IS NOT NULL THEN COALESCE(sla.end_date, TIMESTAMPTZ '9999-12-31 23:59:59+00')
                WHEN dla.id IS NOT NULL THEN COALESCE(dla.end_date, TIMESTAMPTZ '9999-12-31 23:59:59+00')
                ELSE NULL
      END AS end_date


    FROM sms_configuration c
         LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = c.id
         LEFT JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = c.id
),


  datastream_mapping AS (
    SELECT
      dsl.datastream_id,
      ct.begin_date,
      ct.end_date,
      ct.is_dynamic,
      ct.action_id

      FROM sms_datastream_link dsl
           JOIN sms_device_mount_action dma ON dsl.device_mount_action_id = dma.id
           JOIN configuration_type ct ON dma.configuration_id = ct.configuration_id
  )



SELECT DISTINCT

    o.datastream_id,
    o.result_time,
    dm.is_dynamic,
    dm.action_id,
    dm.begin_date


FROM vo_demogroup_887a7030491444e0aee126fbc215e9f7.observation o
    LEFT JOIN datastream_mapping dm ON o.datastream_id = dm.datastream_id
                                            AND o.result_time >= dm.begin_date
                                            AND o.result_time <= dm.end_date
    WHERE is_dynamic IS NOT NULL
      AND action_id IS NOT NULL;
