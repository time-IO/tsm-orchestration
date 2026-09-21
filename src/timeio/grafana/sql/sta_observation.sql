-- Observations for a single STA datastream linking, restricted to the linking's
-- validity window (begin_date/end_date). One panel repeats over $sta_datastream,
-- so each panel resolves its own linking via the selected link id.
WITH lnk AS (
    SELECT ds_id, begin_date, end_date
    FROM sta_datastream_links
    WHERE link_id = ${{sta_datastream}}
    AND t_uuid :: text = '{uuid}'
),
date_filtered AS (
-- This query returns the data chosen by the datepicker (clamped to the linking's
-- validity window), or returns null if no data is in the selected date range.
    SELECT
        o.result_time AS "time",
        o.result_number AS "value"
    FROM observation o CROSS JOIN lnk
    WHERE $__timeFilter(o.result_time)
    AND o.datastream_id = lnk.ds_id
    AND o.result_time >= lnk.begin_date
    AND (lnk.end_date IS NULL OR o.result_time <= lnk.end_date)
    ORDER BY o.result_time DESC
    LIMIT 1000000  -- 1M
),
fallback AS (
-- This query returns the most recent 10k datapoints within the linking window.
    SELECT
        o.result_time AS "time",
        o.result_number AS "value"
    FROM observation o CROSS JOIN lnk
    WHERE o.datastream_id = lnk.ds_id
    AND o.result_time >= lnk.begin_date
    AND (lnk.end_date IS NULL OR o.result_time <= lnk.end_date)
    ORDER BY o.result_time DESC  -- most recent
    LIMIT 10000  -- 10k
)
-- First the date_filtered query is executed. If it returns null, because the
-- user selected a time range without any data (common for the disjunct time
-- ranges of consecutive settings), the fallback query returns the most recent
-- 10k data points. This fallback data is not shown immediately, but grafana
-- shows a "Zoom to Data" button that jumps to the fallback data on click.
SELECT * FROM date_filtered
UNION ALL
SELECT * FROM fallback
WHERE NOT EXISTS (SELECT 1 FROM date_filtered)
ORDER BY "time" ASC
