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
        seq_name := quote_ident(r.table_schema) || '.' || quote_ident('observation_id_seq');
        constraint_name := quote_ident('pk_observation');

        RAISE NOTICE 'Migrating schema: %', r.table_schema;

        -- 1. Add column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = r.table_schema
              AND table_name = r.table_name
              AND column_name = 'id'
        ) THEN
            RAISE NOTICE 'Adding id column to table: %', full_table;
            EXECUTE format('ALTER TABLE %s ADD COLUMN id BIGINT;', full_table);

            RAISE NOTICE 'Creating sequence: %', seq_name;
            EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %s;', seq_name);

            RAISE NOTICE 'Populating the id column: %', seq_name;
            EXECUTE format(
                'UPDATE %s SET id = nextval(''%s'') WHERE id IS NULL;',
                full_table, r.table_schema || '_observation_id_seq'
            );

            RAISE NOTICE 'Setting default on id column to use sequence';
            EXECUTE format(
                'ALTER TABLE %s ALTER COLUMN id SET DEFAULT nextval(''%s'');',
                full_table, r.table_schema || '_observation_id_seq'
            );

            RAISE NOTICE 'Setting ownership of sequence to id column';
            EXECUTE format(
                'ALTER SEQUENCE %s OWNED BY %s.id;',
                seq_name, full_table
            );

            RAISE NOTICE 'Adding constraint % to table %', constraint_name, full_table;
            EXECUTE format(
                'ALTER TABLE %s ADD CONSTRAINT %s PRIMARY KEY (id);',
                full_table, constraint_name
            );
        END IF;
    END LOOP;
END
$$;
