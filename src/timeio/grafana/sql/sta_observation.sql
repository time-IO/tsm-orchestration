-- Observations of one STA datastream from the "OBSERVATIONS" view, which already
-- clamps them to the link and location validity windows, like FROST. Repeats over
-- $sta_datastream (one panel per datastream).
WITH sel AS (
    SELECT sta_datastream_id AS id
    FROM sta_datastream_links
    -- NULLIF guards the empty-variable phantom panel (no datastreams) from erroring
    WHERE sta_datastream_id = NULLIF('${{sta_datastream}}', '') :: int
    AND t_uuid :: text = '{uuid}'
),
date_filtered AS (
    SELECT
        o."PHENOMENON_TIME_START" AS "time",
        o."RESULT_NUMBER" AS "value"
    FROM "OBSERVATIONS" o
    WHERE $__timeFilter(o."PHENOMENON_TIME_START")
    AND o."DATASTREAM_ID" = (SELECT id FROM sel)
    ORDER BY o."PHENOMENON_TIME_START" DESC
    LIMIT 1000000
),
fallback AS (
    SELECT
        o."PHENOMENON_TIME_START" AS "time",
        o."RESULT_NUMBER" AS "value"
    FROM "OBSERVATIONS" o
    WHERE o."DATASTREAM_ID" = (SELECT id FROM sel)
    ORDER BY o."PHENOMENON_TIME_START" DESC
    LIMIT 10000
)
-- fallback (most recent 10k) only when date_filtered is empty -> "Zoom to Data" button
SELECT * FROM date_filtered
UNION ALL
SELECT * FROM fallback
WHERE NOT EXISTS (SELECT 1 FROM date_filtered)
ORDER BY "time" ASC
