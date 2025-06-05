-- This program adds a primary key column called `id` to the `observation` tables in all schemas.
-- NOTE: For large tables this might take up to a few hours.
DO $$
DECLARE
    r RECORD;
    full_table TEXT;
    seq_name TEXT;
    constraint_name TEXT;
BEGIN
    FOR r IN
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name = 'observation'
          AND table_type = 'BASE TABLE'
    LOOP
        full_table := quote_ident(r.table_schema) || '.' || quote_ident(r.table_name);
        seq_name := quote_ident(r.table_schema || '_observation_id_seq');
        constraint_name := quote_ident('pk_' || r.table_schema || '_observation');

        -- 1. Add column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = r.table_schema
              AND table_name = r.table_name
              AND column_name = 'id'
        ) THEN
            EXECUTE format('ALTER TABLE %s ADD COLUMN id BIGINT;', full_table);

            -- 2. Create the sequence if it doesn't exist
            EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %s;', seq_name);

            -- 3. Populate the 'id' column
            EXECUTE format(
                'UPDATE %s SET id = nextval(''%s'') WHERE id IS NULL;',
                full_table, seq_name
            );

            -- 4. Add primary key constraint
            EXECUTE format(
                'ALTER TABLE %s ADD CONSTRAINT %s PRIMARY KEY (id);',
                full_table, constraint_name
            );
        END IF;
    END LOOP;
END
$$;
