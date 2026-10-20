-- Get last result time by ingest type for a given schema, limited to a time interval.
-- Reads the ingest types from dsm_db instead of the legacy config_db, which
-- does not know things created via the data-source-management. The labels of
-- the legacy ingest types are kept ('extsftp', external API type names).
CREATE OR REPLACE FUNCTION ${monitoring_db_user}.get_latest_observation_by_ingest_type_for_schema(
  p_schema text,
  p_interval interval DEFAULT '24 hours'
)
RETURNS TABLE (ingest_type text, last_result_time timestamptz)
LANGUAGE plpgsql
STABLE SECURITY DEFINER
AS $$
DECLARE
  sql_text text;
BEGIN
  sql_text := format($f$
    SELECT
      (CASE i.ingest_type
        WHEN 'external_api' THEN COALESCE(api.api_type, 'extapi')
        WHEN 'external_sftp' THEN 'extsftp'
        ELSE i.ingest_type
      END)::text AS ingest_type,
      MAX(o.result_time) AS last_result_time
    FROM dsm_db.ingest i
    JOIN %I.thing t ON i.uuid = t.uuid
    JOIN %I.datastream ds ON t.id = ds.thing_id
    LEFT JOIN dsm_db.ingest_external_api api ON api.ingest_id = i.id
    JOIN %I.observation o ON ds.id = o.datastream_id
    WHERE o.result_time >= NOW() - $1
      AND o.result_time IS NOT NULL
    GROUP BY 1
    ORDER BY 1
  $f$, p_schema, p_schema, p_schema);
  RETURN QUERY EXECUTE sql_text USING p_interval;
END;
$$;
