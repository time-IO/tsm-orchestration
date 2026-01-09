DROP VIEW IF EXISTS "NEW_FEATURES" CASCADE;
CREATE VIEW "NEW_FEATURES" AS


SELECT
    crd.feature_id AS "ID",
 	CONCAT(crd.c_label, '_', crd.begin_date) AS "NAME",
 	    CASE
 	        WHEN crd.is_dynamic IS FALSE THEN 'static'
 	            ELSE 'dynamic'
 	        END AS "DESCRIPTION",
to_jsonb(format('{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": %s
  }
}', crd.coordinates)::text) AS "FEATURE",
 '{}'::jsonb  AS "PROPERTIES"

FROM foi_ts_coordinates crd
;

