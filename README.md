# Data Source Management

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


### Authentication
- The frontend application (single page application) authenticates against the Identity Provider (IDP) using authorization code flow with proof key for code exchange (pkce)
- The frontend application receives an id token, access token and a refresh token  
  - The refresh token is used to get new tokens by the idp
  - The id token does nearly not include any information
  - The access token is used as a bearer token in the authorization header in each request to the api
- The api receives a request by the frontend, which includes the access token
- The api verifies that the token signature is correct
  - The api therefore requests the sign keys by the IDP
- The api verifies that the token is issued by the IDP (issuer) and that the token is issued for the frontend (audience)
- The api uses the `sub` claim in the token to find the user in its database
  - If the api can't find a corresponding user, it will be created using the information provided by the userinfo endpoint of the idp 
- The user is authenticated and can be used in the requests
- To get any information about the logged-in user, the frontend needs to make an additional request to the api, to retrieve the stored information of the user

Potential Improvements:  
- The current implementation of the auth flow of the api is implemented synchronously
- It could be improved using an asynchronous method

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