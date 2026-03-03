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
            'ALTER TABLE %I.datastream ADD COLUMN IF NOT EXISTS mutable BOOLEAN NOT NULL DEFAULT FALSE',
            schema_name
        );
    END LOOP;
END $$;
