-- Helper view ts_action_type determines the action type (static or dynamic)
-- and the action ID (ID from sms_configuration_static / dynamic_location_begin_action).
-- with arguments for the observation-View

DROP VIEW IF EXISTS obs_ts_action_type CASCADE;
CREATE VIEW obs_ts_action_type AS


WITH configuration_type AS (
  SELECT
  dsl.datastream_id,
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
    o.id AS o_id,
    o.datastream_id AS o_datastream_id,
    o.result_time,
    ct.is_dynamic,
    ct.action_id,
    ct.begin_date,
    o.result_boolean,
    o.result_quality,
    o.result_string,
    o.result_json,
    o.result_number,
    o.valid_time_start,
    o.result_type,
    o.valid_time_end


FROM observation o
    LEFT JOIN configuration_type ct ON o.datastream_id = ct.datastream_id
                                            AND o.result_time >= ct.begin_date
                                            AND o.result_time <= ct.end_date
    WHERE is_dynamic IS NOT NULL
      AND action_id IS NOT NULL

ORDER BY o_id;
