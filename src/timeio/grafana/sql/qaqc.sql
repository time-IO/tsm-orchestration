SELECT o.result_time AS "time",
1 AS "quality_flag",
jsonb_build_object(
    'annotation',
        CAST(result_quality -> 'resultQuality' -> 'primaryQualityMeasurement' ->> 'value' AS DECIMAL),
    'measure',
        result_quality -> 'resultQuality' -> 'primaryQualityMeasurement' ->> 'metric',
    'parameters',
        result_quality -> 'resultQuality' -> 'primaryQualityMeasurement' -> 'parameters'
) AS "qaqc_result"
FROM observation o
WHERE o.datastream_id = (
    SELECT dp.ds_id
    FROM datastream_properties dp
    WHERE ${{datastream_pos:singlequote}} in (dp.property,dp.position)
    AND dp.t_uuid::text = '{uuid}'
) AND ${{show_qaqc_flags}} = 'True'
AND result_quality IS NOT NULL
AND result_quality <> 'null'
AND result_quality -> 'resultQuality' -> 'primaryQualityMeasurement' ->> 'value' IS NOT NULL
AND result_quality -> 'resultQuality' -> 'primaryQualityMeasurement' ->> 'value' NOT IN ('0.0', '-inf')
ORDER BY o.result_time ASC
