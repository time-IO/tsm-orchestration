CREATE ROLE ${mqtt_monitoring_db_user} WITH LOGIN PASSWORD '${mqtt_monitoring_db_password}';
GRANT ${mqtt_monitoring_db_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS ${mqtt_monitoring_db_user} AUTHORIZATION ${mqtt_monitoring_db_user};
SET search_path TO ${mqtt_monitoring_db_user};
GRANT CONNECT ON DATABASE ${flyway:database} TO ${mqtt_monitoring_db_user};
ALTER ROLE ${mqtt_monitoring_db_user} SET search_path to ${mqtt_monitoring_db_user};
GRANT USAGE ON SCHEMA ${mqtt_monitoring_db_user} TO ${mqtt_monitoring_db_user};

SET SEARCH_PATH TO ${mqtt_monitoring_db_user};

CREATE TABLE broker (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    uptime BIGINT,
    messages_stored INTEGER,
    messages_received INTEGER,
    messages_received_1min FLOAT,
    messages_received_5min FLOAT,
    messages_received_15min FLOAT,
    messages_sent INTEGER,
    messages_sent_1min FLOAT,
    messages_sent_5min FLOAT,
    messages_sent_15min FLOAT,
    messages_retained INTEGER,
    bytes_stored BIGINT,
    bytes_received BIGINT,
    bytes_received_1min BIGINT,
    bytes_received_5min BIGINT,
    bytes_received_15min BIGINT,
    bytes_sent BIGINT,
    bytes_sent_1min BIGINT,
    bytes_sent_5min BIGINT,
    bytes_sent_15min BIGINT,
    clients_total INTEGER,
    clients_active INTEGER,
    clients_inactive INTEGER,
    clients_disconnected INTEGER,
    connections_1min FLOAT,
    connections_5min FLOAT,
    connections_15min FLOAT,
    subscriptions_count INTEGER,
    heap_current BIGINT
);

GRANT SELECT ON ALL TABLES IN SCHEMA ${mqtt_monitoring_db_user} TO ${mqtt_monitoring_db_user};
