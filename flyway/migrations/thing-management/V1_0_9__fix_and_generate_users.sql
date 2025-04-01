-- 1) Rename "name" column to "username"
ALTER TABLE "user"
    RENAME COLUMN "name" TO "username";

-- 2) Fix "user" sequence before inserting
SELECT setval(pg_get_serial_sequence('"user"', 'id'), COALESCE(MAX(id), 0) + 1, FALSE)
FROM "user";

-- 3) Insert 10 new users with "username", avoiding duplicates
INSERT INTO "user" ("username", "password", "first_name", "last_name", "email")
SELECT 'auto_user_' || g.id,
       'pw_' || g.id,
       'Auto' || g.id,
       'User' || g.id,
       'auto_user_' || g.id || '@example.com'
FROM generate_series(1, 10) AS g(id)
WHERE NOT EXISTS (SELECT 1
                  FROM "user"
                  WHERE "username" = 'auto_user_' || g.id);

-- 4) Fix "user" sequence after insertion
SELECT setval(pg_get_serial_sequence('"user"', 'id'), COALESCE(MAX(id), 1) + 1, FALSE)
FROM "user";
