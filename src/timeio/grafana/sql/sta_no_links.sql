-- Drives the "No STA linkings available." info panel: returns exactly one row
-- when this thing has no STA datastream linkings, and no rows otherwise. A text
-- panel repeats over this variable, so the info text shows iff there are none
-- and disappears as soon as at least one linking exists.
SELECT 'No STA linkings available.'
WHERE NOT EXISTS (
    SELECT 1 FROM sta_datastream_links WHERE t_uuid::text = '{uuid}'
)
