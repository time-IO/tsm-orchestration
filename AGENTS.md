# AGENTS.md

## Repository Structure

- `api/` - FastAPI backend (Python). Entry point: `api/app/main.py`
- `frontend/` - Quasar/Vue 3 SPA (TypeScript). Config: `frontend/app/quasar.config.ts`
- `docker-compose.yml` - Full stack (API, frontend, Keycloak, PostgreSQL, MQTT, nginx proxy)

## Development Setup

```bash
docker compose build
docker compose run --rm -u $UID frontend npm ci  # install frontend deps
# Edit /etc/hosts: add "127.0.0.1 proxy"
docker compose up -d
```

- Frontend: http://localhost
- API: http://localhost/api (docs at http://localhost/api/docs)
- Keycloak: http://localhost/keycloak
- Dozzle logs: http://localhost/dozzle

## Commands

### Frontend (`frontend/app/`)

```bash
npm run lint      # ESLint
npm run lint:ts   # vue-tsc --noEmit
npm run lint:all  # lint && lint:ts
npm run format    # prettier --write
npm run dev       # quasar dev
```

### API

```bash
# Format Python with black
docker run --rm --volume $(pwd)/api/app:/src --workdir /src pyfound/black:latest_release black .

# Create Alembic migration (runs via docker compose)
./api/create_alembic_migration.sh <slug>

# Run tests
docker compose run --rm -u $UID --entrypoint "" api pytest
```

### CI Pipeline (.gitlab-ci.yml)

Order: `freeze → check (black, npm-lint, npm-test) → build → release`

- `npm-test` currently exits 0 with no actual tests
- Black check: `black --check api/app/`

## Environment Variables

**API** (`api/app/config.py` > `Settings` class): define in `Settings`, use via `settings` instance.

**Frontend** (`frontend/app/quasar.config.ts` > `build.env`): use `process.env.<KEY>` at runtime.

**Important:** Frontend env vars use placeholder pattern for runtime substitution:

```typescript
const ENV_API_BASE_URL =
  process.env.API_BASE_URL || "ENV_API_BASE_URL_PLACEHOLDER";
```

During build, missing vars become `<KEY>_PLACEHOLDER` strings. The generic frontend image's entrypoint replaces these at container startup.

## Database Migrations

- Tool: Alembic (scripts in `api/app/alembic/versions/`)
- Naming: `YYYYmmdd_HHMMSS_<slug>.py`
- API startup (`api/app/start.sh`) runs `alembic upgrade head` automatically
- Black formatting applied to migrations via alembic.ini post-write hook

## Auth Architecture

- Frontend authenticates via OIDC/PKCE against Keycloak
- Access token sent as Bearer to API
- API validates token signature by fetching keys from IDP
- Users auto-created from IDP userinfo if not in DB
- Permission groups from `eduperson_entitlement` claim

**Permission group entitlement format:** `a:a:a:group:<VO Name>:<Group Name>#`

- VO names must be in `ALLOWED_VOS` env var (comma-separated)

## API Router Order

Router inclusion order in `api/app/main.py` defines OpenAPI doc order. Edit imports and `app.include_router()` calls together.

## Model/Repository Pattern

- Models in `api/app/models/`
- Filters in `api/app/models/filters/`
- Routers in `api/app/routers/`
- Services in `api/app/services/`

## Testing

- No frontend tests configured (`npm test` is a placeholder)
- Backend tests run via: `docker compose run --rm -u $UID --entrypoint "" api pytest`
