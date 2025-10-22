-- Helper view ts_action_type determines the action type (static or dynamic)
-- and the action ID (ID from sms_configuration_static / dynamic_location_begin_action).

DROP VIEW IF EXISTS foi_ts_action_type CASCADE;
CREATE VIEW foi_ts_action_type AS


WITH configuration_type AS (
  SELECT
    dsl.datastream_id,
    c.label AS c_label,
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
                WHEN sla.id IS NOT NULL THEN COALESCE(sla.end_date, 'infinity'::timestamp)
                WHEN dla.id IS NOT NULL THEN COALESCE(dla.end_date, 'infinity'::timestamp)
                ELSE NULL
      END AS end_date


   FROM sms_datastream_link dsl
           JOIN sms_device_mount_action dma ON dsl.device_mount_action_id = dma.id
           JOIN public.sms_device d ON d.id = dma.device_id
           JOIN public.sms_configuration c ON c.id = dma.configuration_id
         LEFT JOIN sms_configuration_static_location_begin_action sla ON sla.configuration_id = c.id
         LEFT JOIN sms_configuration_dynamic_location_begin_action dla ON dla.configuration_id = c.id
    WHERE c.is_public AND d.is_public AND dsl.datasource_id = '{tsm_schema}'s
)

SELECT DISTINCT

    o.datastream_id,
    o.result_time,
    ct.is_dynamic,
    ct.action_id,
    ct.begin_date,
    ct.c_label


FROM observation o
    LEFT JOIN configuration_type ct ON o.datastream_id = ct.datastream_id
                                            AND o.result_time >= ct.begin_date
                                            AND o.result_time <= ct.end_date
    WHERE is_dynamic IS NOT NULL
      AND action_id IS NOT NULL;
