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
- To format the python files of the api using the black formatter, you can use the following docker command:
```
docker run --rm --volume $(pwd)/api/app:/src --workdir /src pyfound/black:latest_release black .   
```

### Environment Variables API
- Environment Variables must be defined in `api/app/config.py` > `Settings` class
- Environment Variables must be used, using the `settings` instance (instantiated at the end of `api/app/config.py`)

### Environment Variables Frontend
- Environment Variables must be defined in `frontend/app/quasar.config.ts`>`build`>`env`
  - afterward they can be used with `process.env.<KEY>`
  - e.g. if you need an example look in the `frontend/app/src/stores/authStore.ts` 

### Auth
- Keycloak
  - accessible at http://localhost/keycloak 
  - well known: http://localhost/keycloak/realms/local-dev/.well-known/openid-configuration

### Data

Should be inserted through migration if necessary.

#### Neutron Monitor Stations
```sql

INSERT INTO neutron_monitor_stations (station_id,description) VALUES
	 ('AATA','Alma-Ata A (R=5.90, Alt=897 m)'),
	 ('AATB','Alma-Ata B (R=5.90, Alt=3340 m)'),
	 ('AHMD','Ahmedabad (R=15.94, Alt=50 m)'),
	 ('APTY','Apatity (R=0.65, Alt=181 m)'),
	 ('ARNM','Aragats (R=7.10, Alt=3200 m)'),
	 ('ATHN','Athens (R=8.53, Alt=260 m)'),
	 ('BKSN','Baksan (R=5.70, Alt=1700 m)'),
	 ('CALG','Calgary (R=1.08, Alt=1123 m)'),
	 ('CALM','NM de Castilla la Mancha (R=6.95, Alt=708 m)'),
	 ('CLMX','Climax (R=3.00, Alt=3400 m)'),
	 ('DJON','Daejeon (R=11.20, Alt=200 m)'),
	 ('DOMB','Dome C mini NM (bare) (R=0.01, Alt=3233 m)'),
	 ('DOMC','Dome C mini NM (R=0.01, Alt=3233 m)'),
	 ('DRBS','Dourbes (R=3.18, Alt=225 m)'),
	 ('ESOI','Emilio Segre Obs. Israel (R=10.75, Alt=2055 m)'),
	 ('FSMT','Fort Smith (R=0.30, Alt=180 m)'),
	 ('HRMS','Hermanus (R=4.58, Alt=26 m)'),
	 ('HUAN','Huancayo (R=12.92, Alt=3400 m)'),
	 ('INVK','Inuvik (R=0.30, Alt=21 m)'),
	 ('IRK2','Irkustk 2 (R=3.64, Alt=2000 m)'),
	 ('IRK3','Irkutsk 3 (R=3.64, Alt=3000 m)'),
	 ('IRKT','Irkustk (R=3.64, Alt=435 m)'),
	 ('JBGO','JangBogo (R=0.30, Alt=29 m)'),
	 ('JUNG','IGY Jungfraujoch (R=4.49, Alt=3570 m)'),
	 ('JUNG1','NM64 Jungfraujoch (R=4.49, Alt=3475 m)'),
	 ('KERG','Kerguelen (R=1.14, Alt=33 m)'),
	 ('KGSN','Kingston (R=1.88, Alt=65 m)'),
	 ('KIEL','Kiel (R=2.36, Alt=54 m)'),
	 ('KIEL2','KielRT (R=2.36, Alt=54 m)'),
	 ('LMKS','Lomnicky Stit (R=3.84, Alt=2634 m)'),
	 ('MCMU','Mc Murdo (R=0.30, Alt=48 m)'),
	 ('MCRL','Mobile Cosmic Ray Laboratory (R=2.46, Alt=200 m)'),
	 ('MGDN','Magadan (R=2.10, Alt=220 m)'),
	 ('MOSC','Moscow (R=2.43, Alt=200 m)'),
	 ('MRNY','Mirny (R=0.03, Alt=30 m)'),
	 ('MWSB','Mawson Bare (R=0.22, Alt=30 m)'),
	 ('MWSN','Mawson (R=0.22, Alt=30 m)'),
	 ('MXCO','Mexico (R=8.28, Alt=2274 m)'),
	 ('NAIN','Nain (R=0.30, Alt=46 m)'),
	 ('NANM','Nor-Amberd (R=7.10, Alt=2000 m)'),
	 ('NEU3','Neumayer III mini neutron monitor (R=0.10, Alt=40 m)'),
	 ('NEWK','Newark (R=2.40, Alt=50 m)'),
	 ('NRLK','Norilsk (R=0.63, Alt=0 m)'),
	 ('NVBK','Novosibirsk (R=2.91, Alt=163 m)'),
	 ('OULU','Oulu (R=0.81, Alt=15 m)'),
	 ('PSNM','Doi Inthanon (Princess Sirindhorn NM) (R=16.80, Alt=2565 m)'),
	 ('PTFM','Potchefstroom (R=6.98, Alt=1351 m)'),
	 ('PWNK','Peawanuck (R=0.30, Alt=53 m)'),
	 ('ROME','Rome (R=6.27, Alt=0 m)'),
	 ('SANB','Sanae D (R=0.73, Alt=52 m)'),
	 ('SNAE','Sanae IV (R=0.73, Alt=856 m)'),
	 ('SOPB','South Pole Bare (R=0.10, Alt=2820 m)'),
	 ('SOPO','South Pole (R=0.10, Alt=2820 m)'),
	 ('TERA','Terre Adelie (R=0.01, Alt=32 m)'),
	 ('THUL','Thule (R=0.30, Alt=26 m)'),
	 ('TSMB','Tsumeb (R=9.15, Alt=1240 m)'),
	 ('TXBY','Tixie Bay (R=0.48, Alt=0 m)'),
	 ('UFSZ','Zugspitze (R=4.10, Alt=2650 m)'),
	 ('YKTK','Yakutsk (R=1.65, Alt=105 m)'),
	 ('ZUGS','Zugspitze (R=4.24, Alt=2960 m)');

```

#### MQTT Parser

```sql
INSERT INTO mqtt_parser(name) values
('Campbell CR6'),
('Schlumberger'),
('campbell_cr6'),
('brightsky_dwd_api'),
('ydoc_ml417'),
('sine_dummy'),
('Gude');
```