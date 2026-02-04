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
  - accessible at http://localhost:8080/keycloak 
  - well known: http://localhost:8080/keycloak/realms/local-dev/.well-known/openid-configuration

### Dummy Data
```sql
INSERT INTO project(name, uuid) VALUES ('Project 1', '1798503646814cc694c384e24cb01b51');

INSERT INTO user(id, username, email, given_name, family_name, active, is_superuser)
VALUES (42,'joedoe','john.doe@foo.bar','john', 'doe',true,false);
```