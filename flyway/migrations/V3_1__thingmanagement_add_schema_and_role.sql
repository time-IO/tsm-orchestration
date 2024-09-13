CREATE ROLE ${thingmanagement_user} WITH LOGIN PASSWORD '${thingmanagement_password}';
GRANT ${thingmanagement_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS thing_management AUTHORIZATION ${thingmanagement_user};
GRANT CONNECT ON DATABASE ${flyway:database} TO ${thingmanagement_user};
ALTER ROLE ${thingmanagement_user} SET search_path TO thing_management;
GRANT USAGE ON SCHEMA thing_management TO ${thingmanagement_user};
GRANT SELECT ON ALL TABLES IN SCHEMA thing_management TO ${thingmanagement_user};