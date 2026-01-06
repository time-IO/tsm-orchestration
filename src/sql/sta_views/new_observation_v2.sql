DROP VIEW IF EXISTS "NEW_OBSERVATIONS" CASCADE;
CREATE VIEW "NEW_OBSERVATIONS" AS


SELECT
    o_id AS "ID",
    result_boolean AS "RESULT_BOOLEAN",
    result_quality AS "RESULT_QUALITY",
    result_time AS "PHENOMENON_TIME_START",
    '{}'::jsonb AS "PARAMETERS",
    device_property_id AS "DATASTREAM_ID",
    result_string AS "RESULT_STRING",
    result_type AS "RESULT_TYPE",
    valid_time_end AS "VALID_TIME_END",
    result_time AS "PHENOMENON_TIME_END",
    feature_id AS "FEATURE ID",
    result_json AS "RESULT_JSON",
    result_time AS "RESULT_TIME",
    result_number AS "RESULT_NUMBER",
    valid_time_start AS "VALID_TIME_START",
'{
  "@context": {
    "@version": "1.1",
    "@import": "stamplate.jsonld",
    "@vocab": "http://schema.org/"
  },
  "jsonld.type": "ObservationProperties",
  "dataSource": null
}'::jsonb AS "PROPERTIES"
FROM obs_ts_coordinates;

