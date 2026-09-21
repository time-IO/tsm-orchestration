-- Template-variable query: one option per STA datastream linking of this thing.
-- __value is the (globally unique) link id, __text the SMS-derived display name.
-- Runs on every dashboard load, so linkings added later appear automatically.
SELECT name AS __text, link_id AS __value
FROM sta_datastream_links
WHERE t_uuid::text = '{uuid}'
-- newest linking first: with a non-"All" multi variable Grafana selects the
-- first option by default, so the current setting shows before historical ones.
ORDER BY begin_date DESC
