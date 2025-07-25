DO $$
DECLARE
  r RECORD;
  schema_name TEXT;
BEGIN
  FOR r IN
    SELECT rolname, unnest(rolconfig) AS config
    FROM pg_roles
    WHERE rolname LIKE 'grf_ro_%'
  LOOP
    IF r.config LIKE 'search_path=%' THEN
      schema_name := trim(split_part(substr(r.config, length('search_path=') + 1), ',', 1));

      EXECUTE format(
        'GRANT SELECT ON %I."LOCATIONS" TO %I;',
        schema_name,
        r.rolname
      );
    END IF;
  END LOOP;
END$$;