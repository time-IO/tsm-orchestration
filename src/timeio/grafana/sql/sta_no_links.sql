-- Always a "Manage linkings in the SMS" link; prefixed with "No STA linkings
-- exist." when this thing has none
SELECT
    CASE WHEN EXISTS (SELECT 1 FROM sta_datastream_links WHERE t_uuid::text = '{uuid}')
         THEN ''
         ELSE 'No STA linkings exist. '
    END || '[Manage datastream linkings in the SMS]({sms_url})' AS msg
