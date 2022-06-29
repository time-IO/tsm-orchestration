
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