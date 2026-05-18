-- drop thing management schema and user
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE ALL ON SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE USAGE ON SCHEMA ${thing_management_db_user} FROM ${thing_management_db_user};
REVOKE CONNECT ON DATABASE ${flyway:database} FROM ${thing_management_db_user};
DROP SCHEMA IF EXISTS ${thing_management_db_user} CASCADE;
REVOKE ${thing_management_db_user} FROM ${flyway:user};
DROP ROLE IF EXISTS ${thing_management_db_user};
