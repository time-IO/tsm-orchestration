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
- visit: http://localhost:3000

### Api
- available under http://localhost:8000
- Documentation: http://localhost:8000/docs 

## Development

### Dummy Data
```sql
INSERT INTO project(name, uuid) VALUES ('Project 1', '1798503646814cc694c384e24cb01b51');

INSERT INTO user(id, username, email, given_name, family_name, active, is_superuser)
VALUES (42,'joedoe','john.doe@foo.bar','john', 'doe',true,false);
```