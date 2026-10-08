-- One option per STA datastream of this thing: __value = "DATASTREAMS"."ID", __text = its name + id
SELECT
    concat("NAME", ' (#', "ID", ')') AS __text,
    "ID" AS __value
FROM "DATASTREAMS"
-- ANY over an ARRAY() param, not IN: only this form is pushed into the view, so
-- it isn't evaluated for every datastream of the project
WHERE "ID" = ANY (ARRAY(
    SELECT sta_datastream_id
    FROM sta_datastream_links
    WHERE t_uuid::text = '{uuid}'
))
ORDER BY "RESULT_TIME_START" DESC, "ID"  -- newest first (default selection)
