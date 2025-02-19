SET search_path TO config_db;

UPDATE file_parser
   SET params = jsonb_set(
     params,
     '{timestamp_columns}',
     COALESCE(
       params->'timestamp_columns',
       jsonb_build_array(
         jsonb_build_object(
           'column', (params->>'timestamp_column')::int,
           'format', params->>'timestamp_format'
         )
       )
     )
   )
 WHERE params ? 'index_col'
   AND params ? 'date_format'
   AND NOT params ? 'timestamp_columns';

UPDATE file_parser
   SET params = params - 'index_col' - 'date_format'
 WHERE params ? 'index_col' OR params ? 'date_format';

