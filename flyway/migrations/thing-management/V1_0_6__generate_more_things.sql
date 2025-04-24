INSERT INTO thing (uuid, name, description, project_id, ingest_type_id, raw_data_storage, created_at, created_by)
SELECT gen_random_uuid(),
       'Thing ' || gs::text,
       'Automated mock thing ' || gs::text,
       (SELECT id FROM project ORDER BY random() LIMIT 1),     -- Random valid project_id
       (SELECT id FROM ingest_type ORDER BY random() LIMIT 1), -- Random valid ingest_type_id
       (random() > 0.5),                                       -- Random boolean for raw_data_storage
       now() - (random() * interval '30 days'),                -- Random date within the last 30 days
       (SELECT id FROM "user" ORDER BY random() LIMIT 1)       -- Random valid created_by user
FROM generate_series(1001, 2000) AS gs;
