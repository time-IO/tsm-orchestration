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
    uptime INTERVAL,
    clients_total INTEGER,
    clients_inactive INTEGER,
    clients_disconnected INTEGER,
    clients_active INTEGER,
    clients_connected INTEGER,
    clients_total INTEGER,
    load_messages_received_1min FLOAT,
    load_messages_received_5min FLOAT,
    load_messages_received_15min FLOAT,
    load_messages_sent_1min FLOAT,
    load_messages_sent_5min FLOAT,
    load_messages_sent_15min FLOAT,
    load_publish_received_1min FLOAT,
    load_publish_received_5min FLOAT,
    load_publish_received_15min FLOAT,
    load_publish_sent_1min FLOAT,
    load_publish_sent_5min FLOAT,
    load_publish_sent_15min FLOAT,
    load_bytes_received_1min FLOAT,
    load_bytes_received_5min FLOAT,
    load_bytes_received_15min FLOAT,
    load_bytes_sent_1min FLOAT,
    load_bytes_sent_5min FLOAT,
    load_bytes_sent_15min FLOAT,
    load_sockets_1min FLOAT,
    load_sockets_5min FLOAT,
    load_sockets_15min FLOAT,
    load_connections_1min FLOAT,
    load_connections_5min FLOAT,
    load_connections_15min FLOAT,
    messages_stored INTEGER,
    messages_received INTEGER,
    messages_sent INTEGER,
    store_messages_count INTEGER,
    store_messages_bytes BIGINT,
    retained_messages_count INTEGER,
    heap_current BIGINT,
    publish_messages_received INTEGER,
    publish_messages_sent INTEGER,
    publish_bytes_received BIGINT,
    publish_bytes_sent BIGINT,
    bytes_received BIGINT,
    bytes_sent BIGINT
);

GRANT SELECT ON ALL TABLES IN SCHEMA ${mqtt_monitoring_db_user} TO ${mqtt_monitoring_db_user};
