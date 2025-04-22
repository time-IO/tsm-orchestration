-- Migration: Update file_parser entries of type CSV (id=1) to valid settings

BEGIN;

UPDATE file_parser
SET settings = jsonb_build_object(
        'column_delimiter', ',',
        'headlines_to_exclude', 1,
        'footer_lines_to_exclude', 1,
        'timestamp_column', 1,
        'timestamp_format', 'YYYY-MM-DD HH24:MI:SS'
               )
WHERE file_parser_type_id = 1;

COMMIT;
