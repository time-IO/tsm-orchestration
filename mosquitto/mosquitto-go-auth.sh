#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE $MQTT_AUTH_POSTGRES_USER WITH LOGIN PASSWORD '$MQTT_AUTH_POSTGRES_PASS';
    GRANT $MQTT_AUTH_POSTGRES_USER TO postgres;
    CREATE SCHEMA IF NOT EXISTS $MQTT_AUTH_POSTGRES_USER AUTHORIZATION $MQTT_AUTH_POSTGRES_USER;
    SET search_path TO $MQTT_AUTH_POSTGRES_USER;
    GRANT CONNECT ON DATABASE postgres TO $MQTT_AUTH_POSTGRES_USER;
    ALTER ROLE $MQTT_AUTH_POSTGRES_USER SET search_path to $MQTT_AUTH_POSTGRES_USER;
    GRANT USAGE ON SCHEMA $MQTT_AUTH_POSTGRES_USER TO $MQTT_AUTH_POSTGRES_USER;
    GRANT ALL ON SCHEMA $MQTT_AUTH_POSTGRES_USER TO $MQTT_AUTH_POSTGRES_USER;

    CREATE TABLE "mqtt_user"
    (
        "id"           bigserial    NOT NULL PRIMARY KEY,
        "project_uuid" uuid         NOT NULL,
        "thing_uuid"   uuid         NOT NULL UNIQUE,
        "username"     varchar(256) NOT NULL,
        "password"     varchar(256) NOT NULL,
        "description"  text         NULL,
        "properties"   jsonb        NULL,
        constraint mqtt_user_project_thing_unique
          unique (project_uuid, thing_uuid)
    );

    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA $MQTT_AUTH_POSTGRES_USER TO $MQTT_AUTH_POSTGRES_USER;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA $MQTT_AUTH_POSTGRES_USER TO $MQTT_AUTH_POSTGRES_USER;
EOSQL