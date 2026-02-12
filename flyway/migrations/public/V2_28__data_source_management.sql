-- create data source management user and schema
CREATE ROLE ${dsm_db_user} WITH LOGIN PASSWORD '${dsm_db_password}';
GRANT ${dsm_db_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS dsm_db AUTHORIZATION ${dsm_db_user};
SET search_path TO dsm_db;
GRANT CONNECT ON DATABASE ${flyway:database} TO ${dsm_db_user};
ALTER ROLE ${dsm_db_user} SET search_path to dsm_db;
GRANT USAGE ON SCHEMA dsm_db TO ${dsm_db_user};
GRANT ALL ON SCHEMA dsm_db TO ${dsm_db_user};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dsm_db TO ${dsm_db_user};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dsm_db TO ${dsm_db_user};

-- drop thing management schema and user
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE ALL ON SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE USAGE ON SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE CONNECT ON DATABASE ${flyway:database} FROM ${thing_management_db_user};
DROP SCHEMA IF EXISTS ${thing_management_db_user} CASCADE;
REVOKE ${thing_management_db_user} FROM ${flyway:user};
DROP ROLE IF EXISTS ${thing_management_db_user};