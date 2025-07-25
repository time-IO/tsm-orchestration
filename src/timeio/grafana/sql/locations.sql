SELECT
  l."LOCATION"::json->'coordinates'->0 AS longitude,
  l."LOCATION"::json->'coordinates'->1 AS latitude,
  t."NAME" as name
FROM "LOCATIONS" l
JOIN "THINGS_LOCATIONS" tl ON l."ID" = tl."LOCATION_ID"
JOIN "THINGS" t ON t."ID" = tl."THING_ID"