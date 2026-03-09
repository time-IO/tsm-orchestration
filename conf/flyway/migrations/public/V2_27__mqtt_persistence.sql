DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOR schema_name IN
        SELECT schemaname
        FROM pg_tables
        WHERE tablename = 'observation'
    LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I.mqtt_message (
                id          BIGSERIAL                NOT NULL PRIMARY KEY,
                "timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,
                message     TEXT                     NOT NULL,
                thing_id    BIGINT                   NOT NULL,

                CONSTRAINT mqtt_message_thing_id_fk_thing_id
                    FOREIGN KEY (thing_id)
                    REFERENCES %I.thing(id)
                    DEFERRABLE INITIALLY DEFERRED
            )',
            schema_name,
            schema_name
        );

        EXECUTE format(
            'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO %I',
            schema_name,
            schema_name
        );
    END LOOP;
END $$;
