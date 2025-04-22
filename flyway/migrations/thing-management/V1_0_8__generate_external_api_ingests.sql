INSERT INTO external_api_ingest (thing_id, api_type_id, sync_interval, sync_enabled, settings)
SELECT t.id,
       -- pick a random existing api_type from external_api_type
       (SELECT id FROM external_api_type ORDER BY random() LIMIT 1) AS api_type_id,
       floor(random() * 60) + 1                                     AS sync_interval,
       (random() > 0.5)                                             AS sync_enabled,
       -- optionally store some random JSON as settings
       jsonb_build_object('info', 'random-' || t.id)                AS settings
FROM (SELECT id
      FROM thing
      WHERE id NOT IN (SELECT thing_id
                       FROM external_api_ingest)
      ORDER BY random()
      LIMIT 500) AS t;
