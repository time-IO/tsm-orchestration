-- Observations for one STA linking, clamped to its validity window. Repeats over
-- $sta_datastream (one panel per linking).
WITH lnk AS (
    SELECT ds_id, begin_date, end_date
    FROM sta_datastream_links
    -- NULLIF guards the empty-variable phantom panel (no linkings) from erroring
    WHERE link_id = NULLIF('${{sta_datastream}}', '') :: int
    AND t_uuid :: text = '{uuid}'
),
date_filtered AS (
    SELECT
        o.result_time AS "time",
        o.result_number AS "value"
    FROM observation o CROSS JOIN lnk
    WHERE $__timeFilter(o.result_time)
    AND o.datastream_id = lnk.ds_id
    AND o.result_time >= lnk.begin_date
    AND (lnk.end_date IS NULL OR o.result_time <= lnk.end_date)
    ORDER BY o.result_time DESC
    LIMIT 1000000
),
fallback AS (
    SELECT
        o.result_time AS "time",
        o.result_number AS "value"
    FROM observation o CROSS JOIN lnk
    WHERE o.datastream_id = lnk.ds_id
    AND o.result_time >= lnk.begin_date
    AND (lnk.end_date IS NULL OR o.result_time <= lnk.end_date)
    ORDER BY o.result_time DESC
    LIMIT 10000
)
-- fallback (most recent 10k) only when date_filtered is empty -> "Zoom to Data" button
SELECT * FROM date_filtered
UNION ALL
SELECT * FROM fallback
WHERE NOT EXISTS (SELECT 1 FROM date_filtered)
ORDER BY "time" ASC
