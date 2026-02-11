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


## Authentication
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

## Permission Groups
- Every entity a user can create with the api, needs to be associated with a permission group
- A user can be member of several permission groups
- The identity provider must provide the information to which permission groups a user belongs via the `eduperson_entitlement` claim
- The name of a permission group in the `eduperson_entitlement` claim must match the pattern `a:a:a:group:<VO Name>:<Group Name>#`
  - `VO Name`: Virtual Organisation Name, a user can belong to several permission groups in several VOs 
  - `Group Name`: Name of the Group, must be unique within the VO
  - example:
  ```
    "eduperson_entitlement": [
      "a:a:a:group:VO:Group1#",
      "a:a:a:group:VO:Group2#"
  ]
   ```
- Permission Groups of VOs, that should be allowed to be used with the api, must be listed in `ALLOWED_VOS` environment variable 

## Generic Frontend Image
### Description
To provide the possibility to set the environment variables for the frontend during runtime we provide a `generic frontend image`. 
### How it works
The key to the solution is how the environment variables in frontend are declared, e.g. `const ENV_API_BASE_URL = process.env.API_BASE_URL || 'ENV_API_BASE_URL_PLACEHOLDER'`.
With `process.env.API_BASE_URL` environment variables can be directly passed. This is useful for development.

During build time no environment variables are passed, therefore all variables will have the `<..._PLACEHOLDER>` string as values, e.g. `const ENV_API_BASE_URL = 'ENV_API_BASE_URL_PLACEHOLDER'`.

The new Dockerfile has an entrypoint script, that searches for these placeholder strings and replaces them with the actual values passed to the container during runtime.

Another challenge is that the several institutes have different configurations for the nginx. The solution is to provide these configuration files as volume mounts in the several deployments. The new image comes with a minimal `default.conf` for the nginx, which can be replaced by volume mounts.

The new image will be added to the container registry and build in the pipeline for every new version.

### How to use it
#### Important
You must provide your own nginx configuration files and mount them to the right places during runtime.
__Important__ is the correct definition of the location of the frontend: 
```
...
  location /data-source-management {
    alias /usr/share/nginx/html/;
    try_files $uri $uri/ /data-source-management/index.html;
  }

...
```

#### Example
Here is an example, how to use it with a minimal nginx configuration file and a docker-compose.yml.
The goal of this example is to make the frontend available under the path `/data-source-management`. 

##### nginx config
`default.conf`:
```
server {
  listen       80;
  listen  [::]:80;
  server_name  localhost;

  location /data-source-management {
    alias /usr/share/nginx/html/;
    try_files $uri $uri/ /data-source-management/index.html;
  }
}

```

##### docker-compose.yml
`docker-compose.yml`

```yaml
services:
  frontend:
    image: registry.hzdr.de/<path to correct registry repo>/data-source-management-generic-frontend-image:1.0.0
    ports:
      - "80:80"
    volumes:
      - "./nginx-example/default.conf:/etc/nginx/conf.d/default.conf"
    environment:
       ENV_API_BASE_URL_PLACEHOLDER: "http://localhost/api"
       ENV_OIDC_IDP_URL_PLACEHOLDER: "https://login-dev.helmholtz.de/oauth2"
       ENV_OIDC_CLIENT_ID_PLACEHOLDER: "timeio-thing-management"
       ENV_OIDC_REDIRECT_URI_PLACEHOLDER: "http://localhost/data-source-management/login-callback"
       ENV_OIDC_SCOPE_PLACEHOLDER: "openid profile eduperson_principal_name eduperson_entitlement eduperson_unique_id email offline_access"
       ENV_OIDC_POST_LOGOUT_REDIRECT_URI_PLACEHOLDER: "http://localhost/data-source-management"
       BASE_URL_ENV_PLACEHOLDER: "data-source-management"

      
      
```

With this setup, you could access the sms under `<my-fancy-domain>/data-source-management`

## Development

### Formatting

```
docker run --rm --volume $(pwd)/api/app:/src --workdir /src pyfound/black:latest_release black .   
```

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