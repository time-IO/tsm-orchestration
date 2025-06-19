-- Add to user table
ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS "authorization_provider_id" VARCHAR(255) UNIQUE;
ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS "username" VARCHAR(255) NOT NULL;
ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS "email" VARCHAR(255);
ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS "first_name" VARCHAR(255);
ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS "last_name" VARCHAR(255);

-- Add to project table
ALTER TABLE "project"
    ADD COLUMN IF NOT EXISTS "authorization_provider_group_id" VARCHAR(255);

-- Create user-project association table if it doesn't exist
CREATE TABLE IF NOT EXISTS "user_project"
(
    "user_id"    BIGINT NOT NULL,
    "project_id" BIGINT NOT NULL,
    PRIMARY KEY ("user_id", "project_id"),
    FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("project_id") REFERENCES "project" ("id") ON DELETE CASCADE
);