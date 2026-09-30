-- One option per STA linking: __value = link id, __text = display name
SELECT name AS __text, link_id AS __value
FROM sta_datastream_links
WHERE t_uuid::text = '{uuid}'
ORDER BY begin_date DESC  -- newest first (default selection)
