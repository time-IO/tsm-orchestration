INSERT INTO ext_sftp_ingest (thing_id, uri, path, "user", password, ssh_priv_key, ssh_pub_key, sync_interval,
                             sync_enabled)
SELECT t.id,
       'sftp://server' || t.id || '.example.com',
       '/data/path' || t.id,
       'user_' || t.id,
       CASE WHEN random() > 0.5 THEN 'password_' || t.id ELSE NULL END,
       CASE WHEN random() > 0.5 THEN 'PRIVATE_KEY_' || t.id ELSE NULL END,
       'PUBLIC_KEY_' || t.id,
       floor(random() * 60) + 1,
       (random() > 0.5)
FROM (SELECT id
      FROM thing
      WHERE id NOT IN (SELECT thing_id FROM ext_sftp_ingest)
      ORDER BY random()
      LIMIT 500) AS t;
