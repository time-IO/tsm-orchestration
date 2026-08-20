# Data Source Management

## Setup

Build Docker images and install node modules

```
docker compose build
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

For Qc-Settings to work on local machine also see: [STA integration](#sta-integration) section in this Readme

### Frontend

- visit: http://localhost/data-source-management

### Api

- available under http://localhost/data-source-management/api
- Documentation: http://localhost/data-source-management/api/docs

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
**Important** is the correct definition of the location of the frontend:

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
  root /usr/share/nginx/html/;

  location /data-source-management {
      alias /usr/share/nginx/html;
      index index.html;
      try_files $uri $uri/ /index.html;
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

#### Api

- To format the python files of the api using the black formatter, you can use the following docker command:

```
docker run --rm --volume $(pwd)/api/app:/src --workdir /src pyfound/black:latest_release black .
```

#### Frontend

- To **check** the .vue and javascript/typescript files using prettier, you can use the following command:

```
docker compose run --rm frontend npx prettier --check .
```

- To **format** the .vue and javascript/typescript files using prettier, you can use the following command:

```
docker compose run --rm frontend npx prettier --write .
```

### Environment Variables API

- Environment Variables must be defined in `api/app/config.py` > `Settings` class
- Environment Variables must be used, using the `settings` instance (instantiated at the end of `api/app/config.py`)

### Environment Variables Frontend

- Environment Variables must be defined in
  - `frontend/app/quasar.config.ts`>`build`>`env`
  - `frontend/docker/generic-image/entrypoint.sh` --> the placeholder string must be added to `environmentPlaceholders`
  - always follow the existing naming structure, e.g. `const ENV_OBJECT_STORAGE_URL = process.env.OBJECT_STORAGE_URL || 'ENV_OBJECT_STORAGE_URL_PLACEHOLDER'`
- afterward they can be used with `process.env.<KEY>`
  - e.g. if you need an example look in the `frontend/app/src/stores/authStore.ts`

### STA integration

- To fill the local STA endpoint with data, [devtools](https://codebase.helmholtz.cloud/ufz-tsm/tsm-dev-tools#dsm-demo-workflow) can be used.
- However, if you wish to test with productive or other external STA data instead:
  - Set the environment variable `STA_ROOT_URL` to the base URL of your desired endpoint (e. g. `https://tsm.ufz.de/sta/`) and restart the service.
  - Update the column `username` in the table `database` to your desired schema/endpoint (e. g. `crnscosmicrayneutronsens_b1b36815413f48ea92ba3a0fbc795f7b`).

### Auth

- Keycloak
  - accessible at http://localhost/keycloak
  - well known: http://localhost/keycloak/realms/local-dev/.well-known/openid-configuration

### Alembic API-DB Migrations

We manage the API-DB (local, stage and prod) using alembic migrations (`api/app/alembic/versions`).
If you applied changes to models that should be propagated to the database, you need to create an alembic migration.

- We use a small script for the creation of the migrations:
  - `./api/create_alembic_migration.sh <slug>`
- The script runs the `api` service with the entrypoint:
  - `alembic revision --autogenerate -m <slug>`
- Every migration created by alembic will have a name in the form of:
  - `YYYYmmdd_HHMMSS_<slug>.py`

### Browser View for Logs

- We've added [dozzle](https://dozzle.dev/)
- To view the container+logs, go to:
  - http://localhost/dozzle

### Datamodel

#### Problem with custom type EncryptedType in alembic migration

When creating a new migration file, alembic will assume that `EncryptedType` is a new type and will try to change the respective columns to that new type.
This **must be manually removed** from the migration file (in `upgrade` **and** `downgrade`).

#### Adding new ingests/parser

- Create the model
- To add a new ingest/parser you will need to update the `CheckConstraint` (`api/app/models/ingest.py` or `api/app/models/parser.py`).
- Create a new migration (pay attention to `Problem with custom type EncryptedType in alembic migration`), drop the existing `CheckConstraint`, create a new one
- Also extend `api/app/constants.py`
- Create the repository

### Generate Dummy Data using SQL

#### Permission Groups

```
DO $$
DECLARE
    i INTEGER := 3;
    max_groups INTEGER := 1000;
    group_uuid UUID;
BEGIN
    WHILE i <= max_groups LOOP
        group_uuid := gen_random_uuid();

        INSERT INTO permission_group (id, name, uuid, entitlement)
        VALUES (
            NEXTVAL('permission_group_id_seq'),
            'VO:group_name_' || i,
            group_uuid,
            'a:a:a:group:VO:group_name_' || i ||'#'
        );

        -- Link this group to user_id = 1
        INSERT INTO permission_group_user_link (permission_group_id, user_id)
        VALUES (CURRVAL('permission_group_id_seq'), 1);

        i := i + 1;
    END LOOP;
END $$;
```

## Quality Control Functions

### Adding a New QC Function

To add a new quality control function to the validation module:

#### 1. Define the Function in `_definition`

Add your function to `api/app/validation/qc_function_definitions.py` in the `_definition` dictionary:

```
"functionName": {
    "description": "Brief description of what the function does",
    "arguments": [
        {
            "name": "arg_name",
            "description": "What this argument does",
            "optional": True/False,
            "default_value": None,
            "types": [
                {"type": "offset", "constraint": {"regex": OFFSET_REGEX}},
                {"type": "float", "constraint": {"min": 0, "max": 100}},
                {"type": "enum", "constraint": {"only": ["option1", "option2"]}},
                # ... other types
            ],
        },
        # ... more arguments
    ],
},
```

**Predefined types available:**

- `OFFSET_TYPE` - Time offset strings (e.g., "1H", "2D")
- `DATASTREAM_TYPE` - List of datastream references
- `BOOL_TYPE` - Boolean values
- `FIELD_ARG` - Standard input field argument
- `TARGET_ARG` / `TARGET_ARG_SIMPLE` - Standard target output argument

#### 2. Add Tests

Create or update tests in `api/app/tests/validation/test_quality_control_constraints.py`:

- Test valid arguments
- Test missing required arguments
- Test invalid argument types
- Test edge cases

Also add tests in `api/app/tests/validation/test_qc_function_definitions.py`:

- Verify function exists in `_definition`
- Verify all arguments have required fields
- Verify enum matches definition keys

#### Validation Rule Summary

**Available types:**

- `datastream` - List/tuple with optional min count
- `float` - Numeric with optional min/max
- `int` - Integer with optional min/max
- `offset` - Time duration string matching offset pattern
- `bool` - Boolean or "true"/"false" string
- `str` - Any string
- `enum` - Value must be in allowed list

**Argument structure:**

```
{
    "name": "argument_name",
    "description": "Description text",
    "optional": False,
    "default_value": None,
    "types": [{"type": "type_name", "constraint": {...}}]
}
```

Run tests after adding: `docker compose run --rm -u $UID --entrypoint "" api pytest`
