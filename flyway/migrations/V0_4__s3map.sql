CREATE ROLE ${s3map_user} WITH LOGIN PASSWORD '${s3map_password}';
GRANT ${s3map_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS ${s3map_user} AUTHORIZATION ${s3map_user};
SET search_path TO ${s3map_user};
GRANT CONNECT ON DATABASE ${flyway:database} TO ${s3map_user};
ALTER ROLE ${s3map_user} SET search_path to ${s3map_user};
GRANT USAGE ON SCHEMA ${s3map_user} TO ${s3map_user};
GRANT ALL ON SCHEMA ${s3map_user} TO ${s3map_user};

CREATE TABLE "mapping" (
    "id"                bigserial    NOT NULL PRIMARY KEY,
    "bucket_name"       varchar(256) NOT NULL UNIQUE,
    "thing_uuid"        uuid         NOT NULL,
    "thing_name"        varchar(256) NOT NULL,
    "db_url"            varchar(256) NOT NULL,
    "filename_pattern"  varchar(256) NULL,
    "parser"            varchar(256) NULL
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ${s3map_user} TO ${s3map_user};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${s3map_user} TO ${s3map_user};