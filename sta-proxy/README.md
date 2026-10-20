# STA Proxy

## Setup

Build Docker images (from the repository root)

```
./dc.sh build sta-proxy-api sta-proxy-frontend
```

## Run

Run with the time.IO orchestration setup.
```
./up.sh
```

For development:
```
./up-with-dev.sh
```

### Frontend

- visit: http://localhost/sta-proxy (or http://localhost/sta)

### Api

- available under http://localhost/sta (STA endpoints, e.g. `http://localhost/sta/<endpoint>/v1.1`)
- the frontend uses the same base URL (`/sta/endpoints`, `/sta/ingests`, `/sta/me`, `/sta/session`)

## Authentication

- The frontend application authenticates against Keycloak using authorization code flow with pkce, see `frontend/app/src/stores/authStore.ts`
- The access token is used as a bearer token in the authorization header in each request to the api
- On login and on every token refresh, the frontend stores the access token in the HttpOnly session cookie `sta_session` (`PUT /sta/session`)
  - A browser tab opening an endpoint URL cannot send a bearer token, so the api uses the cookie instead
- Scripts send the token in the authorization header, anonymous requests send nothing
- The api does not verify tokens itself, it passes them as is to the DSM API (`/me/`, `/permission-group/`)
  - **Currently, the DSM API alone decides which user and permission groups a token belongs to**

## Permission Groups

- Permission groups and memberships are managed by the DSM API, see [data-source-management/README.md](../data-source-management/README.md)
- Every FROST endpoint belongs to a permission group, the endpoint name equals the `database_username` of the group
- A user may read the internal data of an endpoint, if the endpoint belongs to one of the user's permission groups
- The permission groups of a token are cached for 60 seconds (`PERMISSION_GROUPS_CACHE_TTL`), so pagination does not query the DSM API for every page

## Generic Frontend Image

### Description

To provide the possibility to set the environment variables for the frontend during runtime we provide a `generic frontend image`.

### How it works

The key to the solution is how the environment variables in frontend are declared, e.g. `const ENV_API_BASE_URL = import.meta.env.API_BASE_URL || 'ENV_API_BASE_URL_PLACEHOLDER'`.
With `import.meta.env.API_BASE_URL` environment variables can be directly passed. This is useful for development.

During build time no environment variables are passed, therefore all variables will have the `<..._PLACEHOLDER>` string as values, e.g. `const ENV_API_BASE_URL = 'ENV_API_BASE_URL_PLACEHOLDER'`.

The Dockerfile has an entrypoint script, that searches for these placeholder strings and replaces them with the actual values passed to the container during runtime.

The image comes with a minimal `default.conf` for the nginx (`frontend/docker/generic-image/`), which can be replaced by volume mounts.

### How to use it

See the `sta-proxy-frontend` service in `docker-compose.yml`, which passes the `ENV_..._PLACEHOLDER` variables, and the `/sta-proxy/` location in `nginx/locations/locations.conf`.

## Development

### Api Tests

Run the api unit tests from the repository root:

```bash
python3 -m pytest sta-proxy/api/app/tests/unit_tests
```

### Formatting

#### Api

- To format the python files of the api using the black formatter, you can use the following docker command (from `sta-proxy/`):

```
docker run --rm --volume $(pwd)/api/app:/src --workdir /src pyfound/black:latest_release black .
```

#### Frontend

- To **check** the .vue and javascript/typescript files using prettier, you can use the following command (from the repository root):

```
./dc-with-dev.sh run --rm sta-proxy-frontend npx prettier --check .
```

- To **format** the .vue and javascript/typescript files using prettier, you can use the following command:

```
./dc-with-dev.sh run --rm sta-proxy-frontend npx prettier --write .
```

### Environment Variables API

- Environment Variables must be defined in `api/app/config.py` > `Settings` class
- Environment Variables must be used, using the `settings` instance (instantiated at the end of `api/app/config.py`)

### Environment Variables Frontend

- Environment Variables must be defined in
  - `frontend/app/quasar.config.ts` > `build` > `defineEnv`
  - `frontend/docker/generic-image/entrypoint.sh` --> the placeholder string must be added to `environmentPlaceholders`
  - always follow the existing naming structure, e.g. `const ENV_SMS_URL = import.meta.env.SMS_URL || 'ENV_SMS_URL_PLACEHOLDER'`
- afterward they can be used with `import.meta.env.<KEY>`
  - e.g. if you need an example look in the `frontend/app/src/boot/axios.ts`

### Auth

- Keycloak
  - accessible at http://localhost/keycloak
  - well known: http://localhost/keycloak/realms/timeio/.well-known/openid-configuration

### Browser View for Logs

- We've added [dozzle](https://dozzle.dev/) to the development setup
- To view the container+logs, go to:
  - http://localhost/dozzle

## Workflows

The components, the layers of the api and the main workflows are shown in [docs/sequence-diagrams.md](docs/sequence-diagrams.md).

### Explicit routes

Besides `/sta/{endpoint}/v1.1/...`, which selects the FROST server by the token, two routes pin the target:

| Route | Target | Checks |
|---|---|---|
| `GET /sta/public/{endpoint}/v1.1/...` | public FROST | none, token and cookie are ignored |
| `GET /sta/internal/{endpoint}/v1.1/...` | internal FROST | token (header or `sta_session` cookie) and permission group |

The internal route never falls back to public data:

- no token, or a token the DSM API rejects: `401`
- user is not in the endpoint's permission group: `403`
- DSM API not reachable: `502`, timeout: `504`

FROST builds its links (`@iot.nextLink`, `@iot.selfLink`, `…@iot.navigationLink`) from its `serviceRootUrl`, which is `STA_PROXY_URL` plus the endpoint name, i.e. the automatic route.
The explicit routes rewrite these links in JSON responses to `<STA_PROXY_URL>public/<endpoint>/` or `<STA_PROXY_URL>internal/<endpoint>/`, so pagination stays on the chosen route.
Bodies of 1 MB and more are rewritten in a worker thread to keep the event loop responsive.
