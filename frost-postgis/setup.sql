
CREATE extension postgres_fdw;

CREATE SERVER tsm FOREIGN DATA WRAPPER postgres_fdw OPTIONS (host 'postgres', dbname 'postgres', port '5432');

CREATE USER MAPPING FOR sensorthings SERVER tsm OPTIONS (user 'postgres', password 'postgres');

CREATE FOREIGN TABLE foreign_table (
        id integer NOT NULL,
        data text
)
        SERVER tsm
        OPTIONS (schema_name 'seefo_envimo_cr6_test_001', table_name 'test');

CREATE SCHEMA seefo_envimo_cr6_test_001;

IMPORT FOREIGN SCHEMA seefo_envimo_cr6_test_001 FROM SERVER tsm INTO seefo_envimo_cr6_test_001;


CREATE VIEW "DATASTREAMS" AS SELECT
    id as "ID",
    name as "NAME",
    description as "DESCRIPTION",
    text '' as "OBSERVATION_TYPE",
    null as "PHENOMENON_TIME_START",
    null as "PHENOMENON_TIME_END",
    null as "RESULT_TIME_START",
    null as "RESULT_TIME_END",
    bigint '1' as "SENSOR_ID",
    bigint '1' as "OBS_PROPERTY_ID",
    thing_id as "THING_ID",
    varchar(255) '' as "UNIT_NAME",
    varchar(255) '' as "UNIT_SYMBOL",
    varchar(255) '' as "UNIT_DEFINITION",
    null as "OBSERVED_AREA",
    properties as "PROPERTIES",
    bigint '0' as "LAST_FOI_ID"
from seefo_envimo_cr6_test_001.datastream;



CREATE VIEW "OBSERVATIONS" AS SELECT
    bigint '1' as "ID",
    phenomenon_time_start as "PHENOMENON_TIME_START",
    phenomenon_time_end as "PHENOMENON_TIME_END",
    result_time as "RESULT_TIME",
    result_number as "RESULT_NUMBER",
    result_string as "RESULT_STRING",
    result_quality as "RESULT_QUALITY",
    valid_time_start as "VALID_TIME_START",
    valid_time_end as "VALID_TIME_END",
    parameters as "PARAMETERS",
    datastream_id as "DATASTREAM_ID",
    bigint '0' as "FEATURE_ID",
    smallint '0' as "RESULT_TYPE",
    null as "RESULT_JSON",
    result_boolean as "RESULT_BOOLEAN",
    bigint '0' as "MULTI_DATASTREAM_ID"
from seefo_envimo_cr6_test_001.observation;

-- *************************************************************************************
-- OBSERVATIONS could be also provided with a GROUP-BY statement to provide for examples results per hour:

-- create view "OBSERVATIONS"
--             ("RESULT_TIME", "DATASTREAM_ID", "ID", "PHENOMENON_TIME_START", "PHENOMENON_TIME_END", "RESULT_NUMBER",
--              "RESULT_STRING", "RESULT_QUALITY", "VALID_TIME_START", "VALID_TIME_END", "PARAMETERS", "FEATURE_ID",
--              "RESULT_TYPE", "RESULT_JSON", "RESULT_BOOLEAN", "MULTI_DATASTREAM_ID")
-- as
-- SELECT date_trunc('hour'::text, observation.result_time) AS "RESULT_TIME",
--        observation.datastream_id                         AS "DATASTREAM_ID",
--        '1'::bigint                                       AS "ID",
--        NULL::timestamp with time zone                    AS "PHENOMENON_TIME_START",
--        NULL::timestamp with time zone                    AS "PHENOMENON_TIME_END",
--        avg(observation.result_number)                    AS "RESULT_NUMBER",
--        NULL::character varying(200)                      AS "RESULT_STRING",
--        '{}'::jsonb                                       AS "RESULT_QUALITY",
--        NULL::timestamp with time zone                    AS "VALID_TIME_START",
--        NULL::timestamp with time zone                    AS "VALID_TIME_END",
--        '{}'::jsonb                                       AS "PARAMETERS",
--        '0'::bigint                                       AS "FEATURE_ID",
--        '0'::smallint                                     AS "RESULT_TYPE",
--        NULL::text                                        AS "RESULT_JSON",
--        NULL::boolean                                     AS "RESULT_BOOLEAN",
--        '0'::bigint                                       AS "MULTI_DATASTREAM_ID"
-- FROM seefo_envimo_cr6_test_001.observation
-- GROUP BY (date_trunc('hour'::text, observation.result_time)), observation.datastream_id;
--
-- alter table "OBSERVATIONS"
--     owner to sensorthings;
