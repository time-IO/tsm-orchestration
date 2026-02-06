# preparation-data-source-management

## Setup
Build Docker Images
```
docker compose build
```
Install node modules
```
docker compose run --rm -u $UID frontend npm ci
```

## Run
```
docker compose up -d
```
### Frontend
- visit: http://localhost

### Api
- available under http://localhost/api
- Documentation: http://localhost/api/docs 

## Development

### Environment Variables Frontend
- Environment Variables must be defined in `frontend/app/quasar.config.ts`>`build`>`env`
  - afterward they can be used with `process.env.<KEY>`
  - e.g. if you need an example look in the `frontend/app/src/stores/authStore.ts` 

### Auth
- Keycloak
  - accessible at http://localhost/keycloak 
  - well known: http://localhost/keycloak/realms/local-dev/.well-known/openid-configuration

### Dummy Data
```sql
INSERT INTO permission_group(name, uuid) VALUES ('Permission Group 1', '1798503646814cc694c384e24cb01b51');

INSERT INTO permission_group(name, uuid) VALUES ('Permission Group 2', '1798503646814cc694c384e24cb01b52');
INSERT INTO permission_group(name, uuid) VALUES ('Permission Group 3', '1798503646814cc694c384e24cb01b53');
INSERT INTO permission_group(name, uuid) VALUES ('Permission Group 4', '1798503646814cc694c384e24cb01b54');

INSERT INTO "user"(id, username, email, given_name, family_name, active, is_superuser)
VALUES (42,'joedoe','john.doe@foo.bar','john', 'doe',true,false);
```