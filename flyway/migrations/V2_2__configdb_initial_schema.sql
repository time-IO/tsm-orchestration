SET search_path TO config_db;

CREATE TABLE "database"(
	"id"			BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"schema"		VARCHAR(200) NOT NULL,
	"user"			VARCHAR(200) NOT NULL,
	"password"		VARCHAR(200) NOT NULL,
	"ro_user"		VARCHAR(200) NOT NULL,
	"ro_password"	VARCHAR(200) NOT NULL
);

CREATE TABLE "project"(
	"id"			BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"name"			VARCHAR(200) NOT NULL,
	"uuid"			UUID NOT NULL,
	"database_id"	BIGINT UNIQUE NOT NULL
);

ALTER TABLE "project" ADD CONSTRAINT "fk_project_db" FOREIGN KEY ("database_id") REFERENCES "database" ("id") DEFERRABLE INITIALLY DEFERRED;


CREATE TABLE "qaqc"(
	"id"		        BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"name"		        VARCHAR(200) NOT NULL,
	"project_id" 	    BIGINT NOT NULL,
	"context_window"	VARCHAR(200) NOT NULL
);

alter TABLE "qaqc" add constraint "fk_qaqc_project" foreign key ("project_id") references "project" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "qaqc_test"(
    "id"		    BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    "target"	    VARCHAR(200) NOT NULL,
    "qaqc_id"       BIGINT NOT NULL,
    "function"      VARCHAR(200) NOT NULL,
    "args"          jsonb NULL
);

alter TABLE "qaqc_test" add constraint "fk_qaqc_test_qaqc" foreign key ("qaqc_id") references "qaqc" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "ext_api_type"(
	"id"	BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"name" 	VARCHAR(200) UNIQUE NOT NULL
);

CREATE TABLE "ext_api"(
	"id"		        BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"api_type_id"	    BIGINT NOT NULL,
	"sync_interval" 	INT NOT NULL,
	"sync_enabled"	    boolean NOT NULL,
	"settings"	        jsonb NULL
);

ALTER TABLE "ext_api" ADD CONSTRAINT "fk_ext_api_ext_api_type" FOREIGN KEY ("api_type_id") REFERENCES "ext_api_type" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "ext_sftp"(
	"id"			BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    "uri"           VARCHAR(200) NOT NULL,
	"path"		    VARCHAR(200) NOT NULL,
	"user"		    VARCHAR(200) NOT NULL,
	"password"	    VARCHAR(200) NOT NULL,
	"ssh_priv_key"	TEXT NOT NULL,
	"ssh_pub_key"	TEXT NOT NULL,
	"sync_interval"	INT NOT NULL,
	"sync_enabled"	boolean NOT NULL
);

CREATE TABLE "mqtt_device_type"(
	"id"	BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"name"	VARCHAR(200) UNIQUE NOT NULL
);

CREATE TABLE "mqtt"(
	"id"			        BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"user"			        VARCHAR(200) NOT NULL,
	"password"		        VARCHAR(200) NOT NULL,
	"password_hashed"	    TEXT NOT NULL,
	"topic"			        VARCHAR(200) NOT NULL,
	"mqtt_device_type_id"	BIGINT NOT NULL

);

ALTER TABLE "mqtt" ADD CONSTRAINT "fk_mqtt_mqtt_device_type" FOREIGN KEY ("mqtt_device_type_id") REFERENCES "mqtt_device_type" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "file_parser_type"(
	"id"	BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"name"	VARCHAR(200) UNIQUE NOT NULL
);

CREATE TABLE "file_parser"(
	"id"					BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"file_parser_type_id"   BIGINT NOT NULL,
	"name"	                VARCHAR(200) NOT NULL,
	"params"	            jsonb NULL
);

ALTER TABLE "file_parser" ADD CONSTRAINT "fk_file_parser_file_parser_type" FOREIGN KEY ("file_parser_type_id") REFERENCES "file_parser_type" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "s3_store"(
	"id"		        BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"user"			    VARCHAR(200) NOT NULL,
	"password"		    VARCHAR(200) NOT NULL,
	"bucket"			VARCHAR(200) NOT NULL,
	"filename_pattern"	VARCHAR(200) NULL,
	"file_parser_id"	BIGINT UNIQUE NOT NULL
);

ALTER TABLE "s3_store" ADD CONSTRAINT "fk_s3_store_file_parser" FOREIGN KEY ("file_parser_id") REFERENCES "file_parser" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE "ingest_type"(
	"id"	BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"name"	VARCHAR(200) UNIQUE NOT NULL
);

CREATE TABLE "thing"(
	"id"		        BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	"uuid"		        UUID NOT NULL,
	"name"		        VARCHAR(200) NOT NULL,
	"project_id" 	    BIGINT NOT NULL,
	"ingest_type_id"	BIGINT NOT NULL,
	"s3_store_id"	    BIGINT UNIQUE NOT NULL,
	"mqtt_id"	        BIGINT UNIQUE NOT NULL,
	"ext_sftp_id"	    BIGINT UNIQUE NULL,
	"ext_api_id"	    BIGINT UNIQUE NULL

);

ALTER TABLE "thing" ADD CONSTRAINT "fk_thing_project" FOREIGN KEY ("project_id") REFERENCES "project" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "thing" ADD CONSTRAINT "fk_thing_ingest_type" FOREIGN KEY ("ingest_type_id") REFERENCES "ingest_type" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "thing" ADD CONSTRAINT "fk_thing_s3_store" FOREIGN KEY ("s3_store_id") REFERENCES "s3_store" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "thing" ADD CONSTRAINT "fk_thing_mqtt" FOREIGN KEY ("mqtt_id") REFERENCES "mqtt" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "thing" ADD CONSTRAINT "fk_thing_ext_sftp" FOREIGN KEY ("ext_sftp_id") REFERENCES "ext_sftp" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "thing" ADD CONSTRAINT "fk_thing_ext_api" FOREIGN KEY ("ext_api_id") REFERENCES "ext_api" ("id") DEFERRABLE INITIALLY DEFERRED;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA config_db TO ${configdb_user};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA config_db TO ${configdb_user};