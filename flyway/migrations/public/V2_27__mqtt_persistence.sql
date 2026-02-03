DO $$
DECLARE
    schema_name TEXT;
BEGIN
    -- Alle Schemata finden, die eine Tabelle "observation" haben
    FOR schema_name IN
        SELECT schemaname
        FROM pg_tables
        WHERE tablename = 'observation'
    LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I.mqtt_message (
                id          BIGSERIAL    NOT NULL PRIMARY KEY,
                message     TEXT         NOT NULL,
                thing_id    BIGINT       NOT NULL,
                CONSTRAINT %I
                    FOREIGN KEY (thing_id)
                    REFERENCES %I.thing(id)
                    DEFERRABLE INITIALLY DEFERRED
            )',
            schema_name,                                          -- Tabellenname qualifizieren
            schema_name || '_mqtt_message_thing_id_fk_thing_id',  -- Constraint-Name eindeutig machen
            schema_name                                           -- FK-Referenz qualifizieren
        );
    END LOOP;
END $$;