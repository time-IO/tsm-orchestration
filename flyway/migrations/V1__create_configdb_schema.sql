CREATE ROLE ${configdb_user} WITH LOGIN PASSWORD '${configdb_password}';
GRANT ${configdb_user} TO ${flyway:user};
CREATE SCHEMA IF NOT EXISTS ${configdb_user} AUTHORIZATION ${configdb_user};
GRANT CONNECT ON DATABASE ${flyway:database} TO ${configdb_user};
ALTER ROLE ${configdb_user} SET search_path TO ${configdb_user};
GRANT USAGE ON SCHEMA ${configdb_user} TO ${configdb_user};
GRANT ALL ON SCHEMA ${configdb_user} TO ${configdb_user};
