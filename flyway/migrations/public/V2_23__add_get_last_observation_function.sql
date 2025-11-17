CREATE FUNCTION ${monitoring_db_user}.get_last_observations()
RETURNS TABLE(schema_name text, result_time timestamptz)
LANGUAGE plpgsql STABLE SECURITY DEFINER AS $$
DECLARE
  sch text;
  qry text;
BEGIN
  FOR sch IN
    SELECT table_schema
    FROM information_schema.tables
    WHERE table_name = 'observation'
      AND table_type = 'BASE TABLE'
      AND table_schema NOT IN ('pg_catalog','information_schema')
  LOOP
    qry := format(
      'SELECT %L::text AS schema_name,
              o.result_time::timestamptz AS result_time
       FROM %I.observation o
       ORDER BY o.id DESC
       LIMIT 1',
      sch, sch
    );
    RETURN QUERY EXECUTE qry;
  END LOOP;
END;
$$;