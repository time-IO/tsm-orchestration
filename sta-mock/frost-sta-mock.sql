--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg110+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: frost
--

CREATE SCHEMA tiger;


ALTER SCHEMA tiger OWNER TO frost;

--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: frost
--

CREATE SCHEMA tiger_data;


ALTER SCHEMA tiger_data OWNER TO frost;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: frost
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO frost;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: frost
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: count_estimate(text); Type: FUNCTION; Schema: public; Owner: frost
--

CREATE FUNCTION public.count_estimate(query text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    rec   record;
    rows  integer;
BEGIN
    FOR rec IN EXECUTE 'EXPLAIN ' || query LOOP
        rows := substring(rec."QUERY PLAN" FROM ' rows=([[:digit:]]+)');
        EXIT WHEN rows IS NOT NULL;
    END LOOP;

    RETURN rows;
END
$$;


ALTER FUNCTION public.count_estimate(query text) OWNER TO frost;

--
-- Name: datastreams_update_delete(); Type: FUNCTION; Schema: public; Owner: frost
--

CREATE FUNCTION public.datastreams_update_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $_$
declare
    "DS_ROW" "DATASTREAMS"%rowtype;
    queryset TEXT := '';
    delimitr char(1) := ' ';
begin

if (OLD."DATASTREAM_ID" is not null)
then
    select * into "DS_ROW" from "DATASTREAMS" where "DATASTREAMS"."ID"=OLD."DATASTREAM_ID";

    if (OLD."PHENOMENON_TIME_START" = "DS_ROW"."PHENOMENON_TIME_START"
        or coalesce(OLD."PHENOMENON_TIME_END", OLD."PHENOMENON_TIME_START") = "DS_ROW"."PHENOMENON_TIME_END")
    then
        queryset := queryset || delimitr || '"PHENOMENON_TIME_START" = (select min("PHENOMENON_TIME_START") from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
        delimitr := ',';
        queryset := queryset || delimitr || '"PHENOMENON_TIME_END" = (select max(coalesce("PHENOMENON_TIME_END", "PHENOMENON_TIME_START")) from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
    end if;

    if (OLD."RESULT_TIME" = "DS_ROW"."RESULT_TIME_START")
    then
        queryset := queryset || delimitr || '"RESULT_TIME_START" = (select min("RESULT_TIME") from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
        delimitr := ',';
    end if;
    if (OLD."RESULT_TIME" = "DS_ROW"."RESULT_TIME_END")
    then
        queryset := queryset || delimitr || '"RESULT_TIME_END" = (select max("RESULT_TIME") from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
        delimitr := ',';
    end if;
    if (delimitr = ',') then
        EXECUTE 'update "DATASTREAMS" SET ' || queryset ||  ' where "DATASTREAMS"."ID"=$1."DATASTREAM_ID"' using OLD;
    end if;
end if;    

return NULL;
end
$_$;


ALTER FUNCTION public.datastreams_update_delete() OWNER TO frost;

--
-- Name: datastreams_update_insert(); Type: FUNCTION; Schema: public; Owner: frost
--

CREATE FUNCTION public.datastreams_update_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $_$
declare
    "DS_ROW" RECORD;
    queryset TEXT := '';
    delimitr char(1) := ' ';
begin

if (NEW."DATASTREAM_ID" is not null)
then
    select "ID","PHENOMENON_TIME_START","PHENOMENON_TIME_END","RESULT_TIME_START","RESULT_TIME_END","OBSERVED_AREA","LAST_FOI_ID"
        into "DS_ROW" from "DATASTREAMS" where "DATASTREAMS"."ID"=NEW."DATASTREAM_ID";
    if (NEW."PHENOMENON_TIME_START"<"DS_ROW"."PHENOMENON_TIME_START" or "DS_ROW"."PHENOMENON_TIME_START" is null) then
        queryset := queryset || delimitr || '"PHENOMENON_TIME_START" = $1."PHENOMENON_TIME_START"';
        delimitr := ',';
    end if;
    if (coalesce(NEW."PHENOMENON_TIME_END", NEW."PHENOMENON_TIME_START") > "DS_ROW"."PHENOMENON_TIME_END" or "DS_ROW"."PHENOMENON_TIME_END" is null) then
        queryset := queryset || delimitr || '"PHENOMENON_TIME_END" = coalesce($1."PHENOMENON_TIME_END", $1."PHENOMENON_TIME_START")';
        delimitr := ',';
    end if;

    if (NEW."RESULT_TIME" is not null) then
        if (NEW."RESULT_TIME"<"DS_ROW"."RESULT_TIME_START" or "DS_ROW"."RESULT_TIME_START" is null) then
            queryset := queryset || delimitr || '"RESULT_TIME_START" = $1."RESULT_TIME"';
            delimitr := ',';
        end if;
        if (NEW."RESULT_TIME" > "DS_ROW"."RESULT_TIME_END" or "DS_ROW"."RESULT_TIME_END" is null) then
            queryset := queryset || delimitr || '"RESULT_TIME_END" = $1."RESULT_TIME"';
            delimitr := ',';
        end if;
    end if;

    if ("DS_ROW"."LAST_FOI_ID" is null or "DS_ROW"."LAST_FOI_ID" != NEW."FEATURE_ID") then
        queryset := queryset || delimitr || '"LAST_FOI_ID" = $1."FEATURE_ID"';
        queryset := queryset || ',"OBSERVED_AREA" = ST_ConvexHull(ST_Collect("OBSERVED_AREA", (select "GEOM" from "FEATURES" where "ID"=$1."FEATURE_ID")))';
        delimitr := ',';
    end if;
    if (delimitr = ',') then
        EXECUTE 'update "DATASTREAMS" SET ' || queryset ||  ' where "DATASTREAMS"."ID"=$1."DATASTREAM_ID"' using NEW;
    end if;
    return new;
end if;

return new;
END
$_$;


ALTER FUNCTION public.datastreams_update_insert() OWNER TO frost;

--
-- Name: datastreams_update_update(); Type: FUNCTION; Schema: public; Owner: frost
--

CREATE FUNCTION public.datastreams_update_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $_$
declare
    "DS_ROW" "DATASTREAMS"%rowtype;
    queryset TEXT := '';
    delimitr char(1) := ' ';
begin

if (NEW."DATASTREAM_ID" is not null)
then
    if (NEW."PHENOMENON_TIME_START" != OLD."PHENOMENON_TIME_START" or NEW."PHENOMENON_TIME_END" != OLD."PHENOMENON_TIME_END") then
        for "DS_ROW" in select * from "DATASTREAMS" where "ID"=NEW."DATASTREAM_ID"
        loop
            if (NEW."PHENOMENON_TIME_START"<"DS_ROW"."PHENOMENON_TIME_START") then
                queryset := queryset || delimitr || '"PHENOMENON_TIME_START" = $1."PHENOMENON_TIME_START"';
                delimitr := ',';
            elseif (OLD."PHENOMENON_TIME_START" = "DS_ROW"."PHENOMENON_TIME_START") then
                queryset := queryset || delimitr || '"PHENOMENON_TIME_START" = (select min("PHENOMENON_TIME_START") from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
                delimitr := ',';
            end if;
            if (coalesce(NEW."PHENOMENON_TIME_END", NEW."PHENOMENON_TIME_START") > "DS_ROW"."PHENOMENON_TIME_END") then
                queryset := queryset || delimitr || '"PHENOMENON_TIME_END" = coalesce($1."PHENOMENON_TIME_END", $1."PHENOMENON_TIME_START")';
                delimitr := ',';
            elseif (coalesce(OLD."PHENOMENON_TIME_END", OLD."PHENOMENON_TIME_START") = "DS_ROW"."PHENOMENON_TIME_END") then
                queryset := queryset || delimitr || '"PHENOMENON_TIME_END" = (select max(coalesce("PHENOMENON_TIME_END", "PHENOMENON_TIME_START")) from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
                delimitr := ',';
            end if;
        end loop;
    end if;


    if (NEW."RESULT_TIME" != OLD."RESULT_TIME") then
        for "DS_ROW" in select * from "DATASTREAMS" where "ID"=NEW."DATASTREAM_ID"
        loop
            if (NEW."RESULT_TIME" < "DS_ROW"."RESULT_TIME_START") then
                queryset := queryset || delimitr || '"RESULT_TIME_START" = $1."RESULT_TIME"';
                delimitr := ',';
            elseif (OLD."RESULT_TIME" = "DS_ROW"."RESULT_TIME_START") then
                queryset := queryset || delimitr || '"RESULT_TIME_START" = (select min("RESULT_TIME") from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
                delimitr := ',';
            end if;
            if (NEW."RESULT_TIME" > "DS_ROW"."RESULT_TIME_END") then
                queryset := queryset || delimitr || '"RESULT_TIME_END" = $1."RESULT_TIME"';
                delimitr := ',';
            elseif (OLD."RESULT_TIME" = "DS_ROW"."RESULT_TIME_END") then
                queryset := queryset || delimitr || '"RESULT_TIME_END" = (select max("RESULT_TIME") from "OBSERVATIONS" where "OBSERVATIONS"."DATASTREAM_ID" = $1."DATASTREAM_ID")';
                delimitr := ',';
            end if;
        end loop;
    end if;
    if (delimitr = ',') then
        EXECUTE 'update "DATASTREAMS" SET ' || queryset ||  ' where "DATASTREAMS"."ID"=$1."DATASTREAM_ID"' using NEW;
    end if;
end if;


return new;
END
$_$;


ALTER FUNCTION public.datastreams_update_update() OWNER TO frost;

--
-- Name: safe_cast_to_boolean(jsonb); Type: FUNCTION; Schema: public; Owner: frost
--

CREATE FUNCTION public.safe_cast_to_boolean(v_input jsonb) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    IF jsonb_typeof(v_input) = 'boolean' THEN
        RETURN (v_input#>>'{}')::boolean;
    ELSE
        RETURN NULL;
    END IF;
END;
$$;


ALTER FUNCTION public.safe_cast_to_boolean(v_input jsonb) OWNER TO frost;

--
-- Name: safe_cast_to_numeric(jsonb); Type: FUNCTION; Schema: public; Owner: frost
--

CREATE FUNCTION public.safe_cast_to_numeric(v_input jsonb) RETURNS numeric
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    IF jsonb_typeof(v_input) = 'number' THEN
        RETURN (v_input#>>'{}')::numeric;
    ELSE
        RETURN NULL;
    END IF;
END;
$$;


ALTER FUNCTION public.safe_cast_to_numeric(v_input jsonb) OWNER TO frost;

--
-- Name: timezone_with_iso_offsets(text, timestamp with time zone); Type: FUNCTION; Schema: public; Owner: frost
--

CREATE FUNCTION public.timezone_with_iso_offsets(zoneid text, tvalue timestamp with time zone) RETURNS timestamp without time zone
    LANGUAGE plpgsql IMMUTABLE
    AS $_$
BEGIN
    IF zoneid ~ '^([+-])?[0-9]{1,2}(:[0-9][0-9](:[0-9][0-9])?)?$' THEN
        IF starts_with(zoneid, '-') THEN
            RETURN timezone(substring(zoneid from 2), tvalue);
        ELSIF starts_with(zoneid, '+') THEN
            RETURN timezone('-' || substring(zoneid from 2), tvalue);
        ELSE
            RETURN timezone('-' || zoneid, tvalue);
        END IF;
    ELSE
        RETURN timezone(zoneid, tvalue);
    END IF;
END;
$_$;


ALTER FUNCTION public.timezone_with_iso_offsets(zoneid text, tvalue timestamp with time zone) OWNER TO frost;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: DATASTREAMS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."DATASTREAMS" (
    "NAME" text,
    "DESCRIPTION" text,
    "PROPERTIES" jsonb,
    "OBSERVATION_TYPE" text,
    "PHENOMENON_TIME_START" timestamp with time zone,
    "PHENOMENON_TIME_END" timestamp with time zone,
    "RESULT_TIME_START" timestamp with time zone,
    "RESULT_TIME_END" timestamp with time zone,
    "OBSERVED_AREA" public.geometry(Geometry,4326),
    "SENSOR_ID" bigint NOT NULL,
    "OBS_PROPERTY_ID" bigint NOT NULL,
    "THING_ID" bigint NOT NULL,
    "UNIT_NAME" character varying(255),
    "UNIT_SYMBOL" character varying(255),
    "UNIT_DEFINITION" character varying(255),
    "LAST_FOI_ID" bigint,
    "ID" bigint NOT NULL
);


ALTER TABLE public."DATASTREAMS" OWNER TO frost;

--
-- Name: DATASTREAMS_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."DATASTREAMS" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."DATASTREAMS_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: FEATURES; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."FEATURES" (
    "NAME" text,
    "DESCRIPTION" text,
    "PROPERTIES" jsonb,
    "ENCODING_TYPE" text,
    "FEATURE" text,
    "GEOM" public.geometry(Geometry,4326),
    "ID" bigint NOT NULL
);


ALTER TABLE public."FEATURES" OWNER TO frost;

--
-- Name: FEATURES_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."FEATURES" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."FEATURES_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: HIST_LOCATIONS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."HIST_LOCATIONS" (
    "TIME" timestamp with time zone,
    "THING_ID" bigint NOT NULL,
    "ID" bigint NOT NULL
);


ALTER TABLE public."HIST_LOCATIONS" OWNER TO frost;

--
-- Name: HIST_LOCATIONS_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."HIST_LOCATIONS" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."HIST_LOCATIONS_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: LOCATIONS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."LOCATIONS" (
    "NAME" text,
    "DESCRIPTION" text,
    "PROPERTIES" jsonb,
    "ENCODING_TYPE" text,
    "LOCATION" text,
    "GEOM" public.geometry(Geometry,4326),
    "GEN_FOI_ID" bigint,
    "ID" bigint NOT NULL
);


ALTER TABLE public."LOCATIONS" OWNER TO frost;

--
-- Name: LOCATIONS_HIST_LOCATIONS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."LOCATIONS_HIST_LOCATIONS" (
    "LOCATION_ID" bigint NOT NULL,
    "HIST_LOCATION_ID" bigint NOT NULL
);


ALTER TABLE public."LOCATIONS_HIST_LOCATIONS" OWNER TO frost;

--
-- Name: LOCATIONS_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."LOCATIONS" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."LOCATIONS_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: OBSERVATIONS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."OBSERVATIONS" (
    "PHENOMENON_TIME_START" timestamp with time zone,
    "PHENOMENON_TIME_END" timestamp with time zone,
    "RESULT_TIME" timestamp with time zone,
    "RESULT_TYPE" smallint,
    "RESULT_NUMBER" double precision,
    "RESULT_BOOLEAN" boolean,
    "RESULT_JSON" jsonb,
    "RESULT_STRING" text,
    "RESULT_QUALITY" jsonb,
    "VALID_TIME_START" timestamp with time zone,
    "VALID_TIME_END" timestamp with time zone,
    "PARAMETERS" jsonb,
    "DATASTREAM_ID" bigint NOT NULL,
    "FEATURE_ID" bigint NOT NULL,
    "ID" bigint NOT NULL
);


ALTER TABLE public."OBSERVATIONS" OWNER TO frost;

--
-- Name: OBSERVATIONS_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."OBSERVATIONS" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."OBSERVATIONS_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: OBS_PROPERTIES; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."OBS_PROPERTIES" (
    "NAME" text,
    "DEFINITION" text,
    "DESCRIPTION" text,
    "PROPERTIES" jsonb,
    "ID" bigint NOT NULL
);


ALTER TABLE public."OBS_PROPERTIES" OWNER TO frost;

--
-- Name: OBS_PROPERTIES_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."OBS_PROPERTIES" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."OBS_PROPERTIES_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: SENSORS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."SENSORS" (
    "NAME" text,
    "DESCRIPTION" text,
    "PROPERTIES" jsonb,
    "ENCODING_TYPE" text,
    "METADATA" text,
    "ID" bigint NOT NULL
);


ALTER TABLE public."SENSORS" OWNER TO frost;

--
-- Name: SENSORS_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."SENSORS" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."SENSORS_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: THINGS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."THINGS" (
    "NAME" text,
    "DESCRIPTION" text,
    "PROPERTIES" jsonb,
    "ID" bigint NOT NULL
);


ALTER TABLE public."THINGS" OWNER TO frost;

--
-- Name: THINGS_ID_seq; Type: SEQUENCE; Schema: public; Owner: frost
--

ALTER TABLE public."THINGS" ALTER COLUMN "ID" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."THINGS_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: THINGS_LOCATIONS; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public."THINGS_LOCATIONS" (
    "THING_ID" bigint NOT NULL,
    "LOCATION_ID" bigint NOT NULL
);


ALTER TABLE public."THINGS_LOCATIONS" OWNER TO frost;

--
-- Name: databasechangelog; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public.databasechangelog (
    id character varying(255) NOT NULL,
    author character varying(255) NOT NULL,
    filename character varying(255) NOT NULL,
    dateexecuted timestamp without time zone NOT NULL,
    orderexecuted integer NOT NULL,
    exectype character varying(10) NOT NULL,
    md5sum character varying(35),
    description character varying(255),
    comments character varying(255),
    tag character varying(255),
    liquibase character varying(20),
    contexts character varying(255),
    labels character varying(255),
    deployment_id character varying(10)
);


ALTER TABLE public.databasechangelog OWNER TO frost;

--
-- Name: databasechangeloglock; Type: TABLE; Schema: public; Owner: frost
--

CREATE TABLE public.databasechangeloglock (
    id integer NOT NULL,
    locked boolean NOT NULL,
    lockgranted timestamp without time zone,
    lockedby character varying(255)
);


ALTER TABLE public.databasechangeloglock OWNER TO frost;

--
-- Data for Name: DATASTREAMS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."DATASTREAMS" ("NAME", "DESCRIPTION", "PROPERTIES", "OBSERVATION_TYPE", "PHENOMENON_TIME_START", "PHENOMENON_TIME_END", "RESULT_TIME_START", "RESULT_TIME_END", "OBSERVED_AREA", "SENSOR_ID", "OBS_PROPERTY_ID", "THING_ID", "UNIT_NAME", "UNIT_SYMBOL", "UNIT_DEFINITION", "LAST_FOI_ID", "ID") FROM stdin;
Temperature Living Room	The temperature in my living room	\N	http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement	2019-03-14 10:00:00+00	2019-03-14 10:05:00+00	\N	\N	0101000020E610000047FAFE1719DA2040FFAECF9CF5814840	1	1	1	Centigrade	C	http://www.qudt.org/qudt/owl/1.0.0/unit/Instances.html#DegreeCentigrade	1	1
Humidity Living Room	The humidity in my living room	\N	http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement	2019-03-14 10:00:00+00	2019-03-14 10:05:00+00	\N	\N	0101000020E610000047FAFE1719DA2040FFAECF9CF5814840	2	2	1	percentage	%	https://en.wikipedia.org/wiki/Percentage	1	2
\.


--
-- Data for Name: FEATURES; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."FEATURES" ("NAME", "DESCRIPTION", "PROPERTIES", "ENCODING_TYPE", "FEATURE", "GEOM", "ID") FROM stdin;
My Living Room	The living room of Fraunhoferstr. 1	\N	application/vnd.geo+json	{"type":"Point","coordinates":[8.4259727,49.015308]}	0101000020E610000047FAFE1719DA2040FFAECF9CF5814840	1
\.


--
-- Data for Name: HIST_LOCATIONS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."HIST_LOCATIONS" ("TIME", "THING_ID", "ID") FROM stdin;
2026-08-06 11:01:38.696+00	1	1
\.


--
-- Data for Name: LOCATIONS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."LOCATIONS" ("NAME", "DESCRIPTION", "PROPERTIES", "ENCODING_TYPE", "LOCATION", "GEOM", "GEN_FOI_ID", "ID") FROM stdin;
My Living Room	The living room of Fraunhoferstr. 1	\N	application/vnd.geo+json	{"type":"Point","coordinates":[8.4259727,49.015308]}	0101000020E610000047FAFE1719DA2040FFAECF9CF5814840	1	1
\.


--
-- Data for Name: LOCATIONS_HIST_LOCATIONS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."LOCATIONS_HIST_LOCATIONS" ("LOCATION_ID", "HIST_LOCATION_ID") FROM stdin;
1	1
\.


--
-- Data for Name: OBSERVATIONS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."OBSERVATIONS" ("PHENOMENON_TIME_START", "PHENOMENON_TIME_END", "RESULT_TIME", "RESULT_TYPE", "RESULT_NUMBER", "RESULT_BOOLEAN", "RESULT_JSON", "RESULT_STRING", "RESULT_QUALITY", "VALID_TIME_START", "VALID_TIME_END", "PARAMETERS", "DATASTREAM_ID", "FEATURE_ID", "ID") FROM stdin;
2019-03-14 10:00:00+00	2019-03-14 10:00:00+00	\N	0	21	\N	\N	21.0	\N	\N	\N	\N	1	1	1
2019-03-14 10:01:00+00	2019-03-14 10:01:00+00	\N	0	21.1	\N	\N	21.1	\N	\N	\N	\N	1	1	2
2019-03-14 10:02:00+00	2019-03-14 10:02:00+00	\N	0	19	\N	\N	19.0	\N	\N	\N	\N	1	1	3
2019-03-14 10:03:00+00	2019-03-14 10:03:00+00	\N	0	19.1	\N	\N	19.1	\N	\N	\N	\N	1	1	4
2019-03-14 10:04:00+00	2019-03-14 10:04:00+00	\N	0	19.2	\N	\N	19.2	\N	\N	\N	\N	1	1	5
2019-03-14 10:05:00+00	2019-03-14 10:05:00+00	\N	0	20	\N	\N	20.0	\N	\N	\N	\N	1	1	6
2019-03-14 10:00:00+00	2019-03-14 10:00:00+00	\N	0	40	\N	\N	40.0	\N	\N	\N	\N	2	1	7
2019-03-14 10:01:00+00	2019-03-14 10:01:00+00	\N	0	39.1	\N	\N	39.1	\N	\N	\N	\N	2	1	8
2019-03-14 10:02:00+00	2019-03-14 10:02:00+00	\N	0	42	\N	\N	42.0	\N	\N	\N	\N	2	1	9
2019-03-14 10:03:00+00	2019-03-14 10:03:00+00	\N	0	41.9	\N	\N	41.9	\N	\N	\N	\N	2	1	10
2019-03-14 10:04:00+00	2019-03-14 10:04:00+00	\N	0	41.8	\N	\N	41.8	\N	\N	\N	\N	2	1	11
2019-03-14 10:05:00+00	2019-03-14 10:05:00+00	\N	0	41	\N	\N	41.0	\N	\N	\N	\N	2	1	12
\.


--
-- Data for Name: OBS_PROPERTIES; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."OBS_PROPERTIES" ("NAME", "DEFINITION", "DESCRIPTION", "PROPERTIES", "ID") FROM stdin;
Temperature	http://www.qudt.org/qudt/owl/1.0.0/quantity/Instances.html#ThermodynamicTemperature	The temperature.	\N	1
Relative Humidity	https://en.wikipedia.org/wiki/Relative_humidity	The relative humidity	\N	2
\.


--
-- Data for Name: SENSORS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."SENSORS" ("NAME", "DESCRIPTION", "PROPERTIES", "ENCODING_TYPE", "METADATA", "ID") FROM stdin;
DHT22/Temperature	Temperature sensor of a DHT22	\N	application/pdf	"https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf"	1
DHT22/Humidity	Relative humidity sensor of a DHT22	\N	application/pdf	"https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf"	2
\.


--
-- Data for Name: THINGS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."THINGS" ("NAME", "DESCRIPTION", "PROPERTIES", "ID") FROM stdin;
Living Room	My Living Room	{"style": "Cozy", "balcony": true}	1
\.


--
-- Data for Name: THINGS_LOCATIONS; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public."THINGS_LOCATIONS" ("THING_ID", "LOCATION_ID") FROM stdin;
1	1
\.


--
-- Data for Name: databasechangelog; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public.databasechangelog (id, author, filename, dateexecuted, orderexecuted, exectype, md5sum, description, comments, tag, liquibase, contexts, labels, deployment_id) FROM stdin;
postgresFunctions.sql	scf	liquibase/core.xml	2026-08-06 11:01:36.133941	1	EXECUTED	9:1f3a4616aef81c10a272ce9f99d1da21	sqlFile path=postgresFunctions.sql		\N	5.0.0	\N	\N	6014095316
2021-01-01-datastreams-1	scf	liquibase/plugincoremodel/tableDatastreams.xml	2026-08-06 11:01:36.660752	2	EXECUTED	9:548d6a417c41b37de04d626111a4daf2	createTable tableName=DATASTREAMS		\N	5.0.0	\N	\N	6014095316
2021-01-01-datastreams-2	scf	liquibase/plugincoremodel/tableDatastreams.xml	2026-08-06 11:01:36.692809	3	EXECUTED	9:2680be32fdd4042aa6e155cdf0b16e95	addColumn tableName=DATASTREAMS		\N	5.0.0	\N	\N	6014095316
2021-01-01-datastreams-3	scf	liquibase/plugincoremodel/tableDatastreams.xml	2026-08-06 11:01:36.699843	4	MARK_RAN	9:58efe9d9e30caf1494c4c296cd32fcf4	addColumn tableName=DATASTREAMS		\N	5.0.0	\N	\N	6014095316
2021-01-01-datastreams-4	scf	liquibase/plugincoremodel/tableDatastreams.xml	2026-08-06 11:01:36.745681	5	EXECUTED	9:ba15f694f0fe475b3162645b4a164866	createIndex indexName=DATASTREAMS_OBS_PROPERTY_ID, tableName=DATASTREAMS; createIndex indexName=DATASTREAMS_SENSOR_ID, tableName=DATASTREAMS; createIndex indexName=DATASTREAMS_THING_ID, tableName=DATASTREAMS		\N	5.0.0	\N	\N	6014095316
2021-01-01-features-1	scf	liquibase/plugincoremodel/tableFeatures.xml	2026-08-06 11:01:36.769517	6	EXECUTED	9:99aba7f8910a3322551a67b6afbec1d7	createTable tableName=FEATURES		\N	5.0.0	\N	\N	6014095316
2021-01-01-features-2	scf	liquibase/plugincoremodel/tableFeatures.xml	2026-08-06 11:01:36.795371	7	EXECUTED	9:f46201ddb39b934e49b8db61432f10a3	addColumn tableName=FEATURES		\N	5.0.0	\N	\N	6014095316
2021-01-01-features-3	scf	liquibase/plugincoremodel/tableFeatures.xml	2026-08-06 11:01:36.800661	8	MARK_RAN	9:72c05d3f65e2ae3156e1d2c26de4c76e	addColumn tableName=FEATURES		\N	5.0.0	\N	\N	6014095316
2021-01-01-histLocations-1	scf	liquibase/plugincoremodel/tableHistLocations.xml	2026-08-06 11:01:36.823649	9	EXECUTED	9:dd835d73ba5a1bb99d0cfb0ac7689195	createTable tableName=HIST_LOCATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-histLocations-2	scf	liquibase/plugincoremodel/tableHistLocations.xml	2026-08-06 11:01:36.842971	10	EXECUTED	9:eff5c1d8e5dac0df9a5a5bda7e352e36	addColumn tableName=HIST_LOCATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-histLocations-3	scf	liquibase/plugincoremodel/tableHistLocations.xml	2026-08-06 11:01:36.848845	11	MARK_RAN	9:d4e06587f0fd53447d6fef9dd867b819	addColumn tableName=HIST_LOCATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-histLocations-4	scf	liquibase/plugincoremodel/tableHistLocations.xml	2026-08-06 11:01:36.874731	12	EXECUTED	9:aa2970a0f09f0af9c796a34d42b568ee	createIndex indexName=HIST_LOCATIONS_THING_ID, tableName=HIST_LOCATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-locations-1	scf	liquibase/plugincoremodel/tableLocations.xml	2026-08-06 11:01:36.903814	13	EXECUTED	9:d4203beae37622dd7ec54aa6ed931ce6	createTable tableName=LOCATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-locations-2	scf	liquibase/plugincoremodel/tableLocations.xml	2026-08-06 11:01:36.928382	14	EXECUTED	9:051ccd9ddd70c1d95344f3864ccd6d67	addColumn tableName=LOCATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-locations-3	scf	liquibase/plugincoremodel/tableLocations.xml	2026-08-06 11:01:36.933646	15	MARK_RAN	9:61a4b939890c65b744ab48f4dc2b9a08	addColumn tableName=LOCATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-locationsHistLocations	scf	liquibase/plugincoremodel/tableLocationsHistLocations.xml	2026-08-06 11:01:36.979944	16	EXECUTED	9:fb436679820198466320105054755e32	createTable tableName=LOCATIONS_HIST_LOCATIONS; addPrimaryKey constraintName=LOCATIONS_HIST_LOCATIONS_PKEY, tableName=LOCATIONS_HIST_LOCATIONS; createIndex indexName=LOCATIONS_HIST_LOCATIONS_HIST_LOCATION_ID, tableName=LOCATIONS_HIST_LOCATIONS; cr...		\N	5.0.0	\N	\N	6014095316
2021-01-01-obsProperties-1	scf	liquibase/plugincoremodel/tableObsProperties.xml	2026-08-06 11:01:37.002505	17	EXECUTED	9:0853686bb9e92c70a1e3205dddc88f54	createTable tableName=OBS_PROPERTIES		\N	5.0.0	\N	\N	6014095316
2021-01-01-obsProperties-2	scf	liquibase/plugincoremodel/tableObsProperties.xml	2026-08-06 11:01:37.027504	18	EXECUTED	9:a558087905b98bed4a9e6c50ebfe08d5	addColumn tableName=OBS_PROPERTIES		\N	5.0.0	\N	\N	6014095316
2021-01-01-obsProperties-3	scf	liquibase/plugincoremodel/tableObsProperties.xml	2026-08-06 11:01:37.031786	19	MARK_RAN	9:2228518450255c0a1dc4b32a6925d7df	addColumn tableName=OBS_PROPERTIES		\N	5.0.0	\N	\N	6014095316
2021-01-01-observations-1	scf	liquibase/plugincoremodel/tableObservations.xml	2026-08-06 11:01:37.057827	20	EXECUTED	9:e460b414f741e5a423a1804467f45a30	createTable tableName=OBSERVATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-observations-2	scf	liquibase/plugincoremodel/tableObservations.xml	2026-08-06 11:01:37.081477	21	EXECUTED	9:5e5094b2ea84f2a9bebfbf23ec47d5aa	addColumn tableName=OBSERVATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-observations-3	scf	liquibase/plugincoremodel/tableObservations.xml	2026-08-06 11:01:37.089834	22	MARK_RAN	9:f5b2f161350ce8a348ee2589d661fc84	addColumn tableName=OBSERVATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-observations-4	scf	liquibase/plugincoremodel/tableObservations.xml	2026-08-06 11:01:37.128332	23	EXECUTED	9:173d7a04dc9c305566236fee4cfbf2f2	createIndex indexName=OBSERVATIONS_DATASTREAM_ID, tableName=OBSERVATIONS; createIndex indexName=OBSERVATIONS_FEATURE_ID, tableName=OBSERVATIONS		\N	5.0.0	\N	\N	6014095316
2021-01-01-sensors-1	scf	liquibase/plugincoremodel/tableSensors.xml	2026-08-06 11:01:37.148382	24	EXECUTED	9:4cc1f6a4af612463bdf688bdaf5e0ab0	createTable tableName=SENSORS		\N	5.0.0	\N	\N	6014095316
2021-01-01-sensors-2	scf	liquibase/plugincoremodel/tableSensors.xml	2026-08-06 11:01:37.168644	25	EXECUTED	9:705ea0a9e0913795a438fa38f37d538d	addColumn tableName=SENSORS		\N	5.0.0	\N	\N	6014095316
2021-01-01-sensors-3	scf	liquibase/plugincoremodel/tableSensors.xml	2026-08-06 11:01:37.172146	26	MARK_RAN	9:1870d7bc06fdee4f6ff308da87d788e0	addColumn tableName=SENSORS		\N	5.0.0	\N	\N	6014095316
2025-04-02-sensors-4	scf	liquibase/plugincoremodel/tableSensors.xml	2026-08-06 11:01:37.180047	27	EXECUTED	9:46ed326d4d76fd3dfbdc84d7a7761d2b	sql		\N	5.0.0	\N	\N	6014095316
2021-01-01-things-1	scf	liquibase/plugincoremodel/tableThings.xml	2026-08-06 11:01:37.200411	28	EXECUTED	9:c7a19083fac76c886db3bf4753eb6617	createTable tableName=THINGS		\N	5.0.0	\N	\N	6014095316
2021-01-01-things-2	scf	liquibase/plugincoremodel/tableThings.xml	2026-08-06 11:01:37.222458	29	EXECUTED	9:ecf17715241afd18ad5c06d8174e1c07	addColumn tableName=THINGS		\N	5.0.0	\N	\N	6014095316
2021-01-01-things-3	scf	liquibase/plugincoremodel/tableThings.xml	2026-08-06 11:01:37.226946	30	MARK_RAN	9:95553009ca5ec5d3f16d9180ad8540ab	addColumn tableName=THINGS		\N	5.0.0	\N	\N	6014095316
2021-01-01-thingsLocations	scf	liquibase/plugincoremodel/tableThingsLocations.xml	2026-08-06 11:01:37.272011	31	EXECUTED	9:1e98694c9ce816107c0327d4821bd82c	createTable tableName=THINGS_LOCATIONS; addPrimaryKey constraintName=THINGS_LOCATIONS_PKEY, tableName=THINGS_LOCATIONS; createIndex indexName=THINGS_LOCATIONS_LOCATION_ID, tableName=THINGS_LOCATIONS; createIndex indexName=THINGS_LOCATIONS_THING_ID...		\N	5.0.0	\N	\N	6014095316
2021-01-01-foreignKeys	scf	liquibase/plugincoremodel/foreignKeys.xml	2026-08-06 11:01:37.325585	32	EXECUTED	9:b1ce45d1e161106c41da4a1c4891d90e	addForeignKeyConstraint baseTableName=DATASTREAMS, constraintName=DATASTREAMS_OBS_PROPERTY_ID_FKEY, referencedTableName=OBS_PROPERTIES; addForeignKeyConstraint baseTableName=DATASTREAMS, constraintName=DATASTREAMS_SENSOR_ID_FKEY, referencedTableNa...		\N	5.0.0	\N	\N	6014095316
2022-04-06-Index-OBS-DS_ID-ID	scf	liquibase/plugincoremodel/foreignKeys.xml	2026-08-06 11:01:37.359243	33	EXECUTED	9:3efe78d906483f293438ba4b3757bf82	createIndex indexName=OBS-DS_ID-ID, tableName=OBSERVATIONS		\N	5.0.0	\N	\N	6014095316
postgresTriggers.sql	scf	liquibase/plugincoremodel/tables.xml	2026-08-06 11:01:37.388159	34	EXECUTED	9:be1cf73c43962439c86a6fc55299c84d	sqlFile path=postgresTriggers.sql		\N	5.0.0	\N	\N	6014095316
\.


--
-- Data for Name: databasechangeloglock; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public.databasechangeloglock (id, locked, lockgranted, lockedby) FROM stdin;
1	f	\N	\N
\.


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: frost
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: geocode_settings; Type: TABLE DATA; Schema: tiger; Owner: frost
--

COPY tiger.geocode_settings (name, setting, unit, category, short_desc) FROM stdin;
\.


--
-- Data for Name: pagc_gaz; Type: TABLE DATA; Schema: tiger; Owner: frost
--

COPY tiger.pagc_gaz (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_lex; Type: TABLE DATA; Schema: tiger; Owner: frost
--

COPY tiger.pagc_lex (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_rules; Type: TABLE DATA; Schema: tiger; Owner: frost
--

COPY tiger.pagc_rules (id, rule, is_custom) FROM stdin;
\.


--
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: frost
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: frost
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- Name: DATASTREAMS_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."DATASTREAMS_ID_seq"', 2, true);


--
-- Name: FEATURES_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."FEATURES_ID_seq"', 1, true);


--
-- Name: HIST_LOCATIONS_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."HIST_LOCATIONS_ID_seq"', 1, true);


--
-- Name: LOCATIONS_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."LOCATIONS_ID_seq"', 1, true);


--
-- Name: OBSERVATIONS_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."OBSERVATIONS_ID_seq"', 12, true);


--
-- Name: OBS_PROPERTIES_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."OBS_PROPERTIES_ID_seq"', 2, true);


--
-- Name: SENSORS_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."SENSORS_ID_seq"', 2, true);


--
-- Name: THINGS_ID_seq; Type: SEQUENCE SET; Schema: public; Owner: frost
--

SELECT pg_catalog.setval('public."THINGS_ID_seq"', 1, true);


--
-- Name: topology_id_seq; Type: SEQUENCE SET; Schema: topology; Owner: frost
--

SELECT pg_catalog.setval('topology.topology_id_seq', 1, false);


--
-- Name: DATASTREAMS DATASTREAMS_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."DATASTREAMS"
    ADD CONSTRAINT "DATASTREAMS_pkey" PRIMARY KEY ("ID");


--
-- Name: FEATURES FEATURES_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."FEATURES"
    ADD CONSTRAINT "FEATURES_pkey" PRIMARY KEY ("ID");


--
-- Name: HIST_LOCATIONS HIST_LOCATIONS_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."HIST_LOCATIONS"
    ADD CONSTRAINT "HIST_LOCATIONS_pkey" PRIMARY KEY ("ID");


--
-- Name: LOCATIONS_HIST_LOCATIONS LOCATIONS_HIST_LOCATIONS_PKEY; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."LOCATIONS_HIST_LOCATIONS"
    ADD CONSTRAINT "LOCATIONS_HIST_LOCATIONS_PKEY" PRIMARY KEY ("LOCATION_ID", "HIST_LOCATION_ID");


--
-- Name: LOCATIONS LOCATIONS_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."LOCATIONS"
    ADD CONSTRAINT "LOCATIONS_pkey" PRIMARY KEY ("ID");


--
-- Name: OBSERVATIONS OBSERVATIONS_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."OBSERVATIONS"
    ADD CONSTRAINT "OBSERVATIONS_pkey" PRIMARY KEY ("ID");


--
-- Name: OBS_PROPERTIES OBS_PROPERTIES_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."OBS_PROPERTIES"
    ADD CONSTRAINT "OBS_PROPERTIES_pkey" PRIMARY KEY ("ID");


--
-- Name: SENSORS SENSORS_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."SENSORS"
    ADD CONSTRAINT "SENSORS_pkey" PRIMARY KEY ("ID");


--
-- Name: THINGS_LOCATIONS THINGS_LOCATIONS_PKEY; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."THINGS_LOCATIONS"
    ADD CONSTRAINT "THINGS_LOCATIONS_PKEY" PRIMARY KEY ("THING_ID", "LOCATION_ID");


--
-- Name: THINGS THINGS_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."THINGS"
    ADD CONSTRAINT "THINGS_pkey" PRIMARY KEY ("ID");


--
-- Name: databasechangeloglock databasechangeloglock_pkey; Type: CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public.databasechangeloglock
    ADD CONSTRAINT databasechangeloglock_pkey PRIMARY KEY (id);


--
-- Name: DATASTREAMS_OBS_PROPERTY_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "DATASTREAMS_OBS_PROPERTY_ID" ON public."DATASTREAMS" USING btree ("OBS_PROPERTY_ID");


--
-- Name: DATASTREAMS_SENSOR_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "DATASTREAMS_SENSOR_ID" ON public."DATASTREAMS" USING btree ("SENSOR_ID");


--
-- Name: DATASTREAMS_THING_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "DATASTREAMS_THING_ID" ON public."DATASTREAMS" USING btree ("THING_ID");


--
-- Name: HIST_LOCATIONS_THING_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "HIST_LOCATIONS_THING_ID" ON public."HIST_LOCATIONS" USING btree ("THING_ID");


--
-- Name: LOCATIONS_HIST_LOCATIONS_HIST_LOCATION_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "LOCATIONS_HIST_LOCATIONS_HIST_LOCATION_ID" ON public."LOCATIONS_HIST_LOCATIONS" USING btree ("HIST_LOCATION_ID");


--
-- Name: LOCATIONS_HIST_LOCATIONS_LOCATION_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "LOCATIONS_HIST_LOCATIONS_LOCATION_ID" ON public."LOCATIONS_HIST_LOCATIONS" USING btree ("LOCATION_ID");


--
-- Name: OBS-DS_ID-ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "OBS-DS_ID-ID" ON public."OBSERVATIONS" USING btree ("DATASTREAM_ID", "ID");


--
-- Name: OBSERVATIONS_DATASTREAM_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "OBSERVATIONS_DATASTREAM_ID" ON public."OBSERVATIONS" USING btree ("DATASTREAM_ID");


--
-- Name: OBSERVATIONS_FEATURE_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "OBSERVATIONS_FEATURE_ID" ON public."OBSERVATIONS" USING btree ("FEATURE_ID");


--
-- Name: THINGS_LOCATIONS_LOCATION_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "THINGS_LOCATIONS_LOCATION_ID" ON public."THINGS_LOCATIONS" USING btree ("LOCATION_ID");


--
-- Name: THINGS_LOCATIONS_THING_ID; Type: INDEX; Schema: public; Owner: frost
--

CREATE INDEX "THINGS_LOCATIONS_THING_ID" ON public."THINGS_LOCATIONS" USING btree ("THING_ID");


--
-- Name: OBSERVATIONS datastreams_actualization_delete; Type: TRIGGER; Schema: public; Owner: frost
--

CREATE TRIGGER datastreams_actualization_delete AFTER DELETE ON public."OBSERVATIONS" FOR EACH ROW EXECUTE FUNCTION public.datastreams_update_delete();


--
-- Name: OBSERVATIONS datastreams_actualization_insert; Type: TRIGGER; Schema: public; Owner: frost
--

CREATE TRIGGER datastreams_actualization_insert AFTER INSERT ON public."OBSERVATIONS" FOR EACH ROW EXECUTE FUNCTION public.datastreams_update_insert();


--
-- Name: OBSERVATIONS datastreams_actualization_update; Type: TRIGGER; Schema: public; Owner: frost
--

CREATE TRIGGER datastreams_actualization_update AFTER UPDATE ON public."OBSERVATIONS" FOR EACH ROW EXECUTE FUNCTION public.datastreams_update_update();


--
-- Name: DATASTREAMS DATASTREAMS_OBS_PROPERTY_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."DATASTREAMS"
    ADD CONSTRAINT "DATASTREAMS_OBS_PROPERTY_ID_FKEY" FOREIGN KEY ("OBS_PROPERTY_ID") REFERENCES public."OBS_PROPERTIES"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: DATASTREAMS DATASTREAMS_SENSOR_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."DATASTREAMS"
    ADD CONSTRAINT "DATASTREAMS_SENSOR_ID_FKEY" FOREIGN KEY ("SENSOR_ID") REFERENCES public."SENSORS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: DATASTREAMS DATASTREAMS_THING_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."DATASTREAMS"
    ADD CONSTRAINT "DATASTREAMS_THING_ID_FKEY" FOREIGN KEY ("THING_ID") REFERENCES public."THINGS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: HIST_LOCATIONS HIST_LOCATIONS_THING_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."HIST_LOCATIONS"
    ADD CONSTRAINT "HIST_LOCATIONS_THING_ID_FKEY" FOREIGN KEY ("THING_ID") REFERENCES public."THINGS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: LOCATIONS_HIST_LOCATIONS LOCATIONS_HIST_LOCATIONS_HIST_LOCATION_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."LOCATIONS_HIST_LOCATIONS"
    ADD CONSTRAINT "LOCATIONS_HIST_LOCATIONS_HIST_LOCATION_ID_FKEY" FOREIGN KEY ("HIST_LOCATION_ID") REFERENCES public."HIST_LOCATIONS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: LOCATIONS_HIST_LOCATIONS LOCATIONS_HIST_LOCATIONS_LOCATION_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."LOCATIONS_HIST_LOCATIONS"
    ADD CONSTRAINT "LOCATIONS_HIST_LOCATIONS_LOCATION_ID_FKEY" FOREIGN KEY ("LOCATION_ID") REFERENCES public."LOCATIONS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: OBSERVATIONS OBSERVATIONS_DATASTREAM_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."OBSERVATIONS"
    ADD CONSTRAINT "OBSERVATIONS_DATASTREAM_ID_FKEY" FOREIGN KEY ("DATASTREAM_ID") REFERENCES public."DATASTREAMS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: OBSERVATIONS OBSERVATIONS_FEATURE_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."OBSERVATIONS"
    ADD CONSTRAINT "OBSERVATIONS_FEATURE_ID_FKEY" FOREIGN KEY ("FEATURE_ID") REFERENCES public."FEATURES"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: THINGS_LOCATIONS THINGS_LOCATIONS_LOCATION_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."THINGS_LOCATIONS"
    ADD CONSTRAINT "THINGS_LOCATIONS_LOCATION_ID_FKEY" FOREIGN KEY ("LOCATION_ID") REFERENCES public."LOCATIONS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: THINGS_LOCATIONS THINGS_LOCATIONS_THING_ID_FKEY; Type: FK CONSTRAINT; Schema: public; Owner: frost
--

ALTER TABLE ONLY public."THINGS_LOCATIONS"
    ADD CONSTRAINT "THINGS_LOCATIONS_THING_ID_FKEY" FOREIGN KEY ("THING_ID") REFERENCES public."THINGS"("ID") ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

