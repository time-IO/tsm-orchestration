-- Using "result_quality -> -1 ->>" because result_quality is an array of quality objects
-- we use "-1" to always select the last one
-- Update: Handle both array [{...}] and object {...} formats for result_quality
SELECT o.result_time AS "time",
    1 AS "quality_flag",
    jsonb_build_object(
        'annotation', CAST (
            CASE
                WHEN jsonb_typeof(result_quality) = 'array'
                THEN result_quality -> -1 ->> 'annotation'
                ELSE result_quality ->> 'annotation'
            END AS DECIMAL
        ),
        'measure',
            CASE
                WHEN jsonb_typeof(result_quality) = 'array'
                THEN result_quality -> -1 -> 'properties' ->> 'measure'
                ELSE result_quality -> 'properties' ->> 'measure'
            END,
        'user_label',
            CASE
                WHEN jsonb_typeof(result_quality) = 'array'
                THEN result_quality -> -1 -> 'properties' ->> 'userLabel'
                ELSE result_quality -> 'properties' ->> 'userLabel'
            END
    ) AS "qaqc_result"
FROM observation o
WHERE o.datastream_id = (
    SELECT dp.ds_id
    FROM datastream_properties dp
    WHERE ${{datastream_pos:singlequote}} in (dp.property,dp.position)
    AND dp.t_uuid::text = '{uuid}'
)
AND ${{show_qaqc_flags}} = 'True'
AND result_quality IS NOT NULL
AND result_quality <> 'null'
AND (
    CASE
        WHEN jsonb_typeof(result_quality) = 'array'
        THEN result_quality -> -1 ->> 'annotation'
        ELSE result_quality ->> 'annotation'
    END
) IS NOT NULL
AND (
    CASE
        WHEN jsonb_typeof(result_quality) = 'array'
        THEN result_quality -> -1 ->> 'annotation'
        ELSE result_quality ->> 'annotation'
    END
) NOT IN ('0.0', '-inf')
ORDER BY o.result_time ASC