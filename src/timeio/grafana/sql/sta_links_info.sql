-- Always a "Manage linkings in the SMS" link; prefixed with "No STA datastreams
-- available." when this thing has none in the STA views (same source as $sta_datastream)
SELECT
    CASE WHEN EXISTS (
            SELECT 1 FROM "DATASTREAMS"
            WHERE "ID" = ANY (ARRAY(
                SELECT sta_datastream_id
                FROM sta_datastream_links
                WHERE t_uuid::text = '{uuid}'
            ))
         )
         THEN ''
         ELSE 'No STA datastreams available. '
    END || '[Manage datastream linkings in the SMS]({sms_url})' AS msg
