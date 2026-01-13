DROP VIEW IF EXISTS "FEATURES" CASCADE;
CREATE VIEW "FEATURES" AS


SELECT
    feature_id AS "ID",
 	CONCAT(label, '_', begin_date) AS "NAME",
 	CASE
 	    WHEN is_dynamic IS FALSE THEN 'static'
 	    ELSE 'dynamic'
 	END AS "DESCRIPTION",
    to_jsonb(format('{
          "type": "Feature",
          "geometry": {
            "type": "Polygon",
            "coordinates": %s
          }
        }', coordinates)::text) AS "FEATURE",
    '{}'::jsonb  AS "PROPERTIES"

FROM foi_ts_action_type_coord
;

