ALTER TABLE ${monitoring_db_user}.mqtt_broker
    ADD COLUMN IF NOT EXISTS packet_out_count DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS packet_out_bytes DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS connections_socket_count DOUBLE PRECISION;
