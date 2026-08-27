# Data Source Management Instructions

These commands assume the orchestration repository root as the working directory and require `docker-compose-dev.yml`; create it from `docker-compose-dev.example.yml` if absent.

## Focused Verification

```bash
# Frontend: ESLint, vue-tsc, then a production build
./dc-with-dev.sh run --rm -u "$UID" dsm-frontend npm run lint:all
./dc-with-dev.sh run --rm -u "$UID" dsm-frontend npm run build

# API checks that do not collect DB-backed integration tests
./dc-with-dev.sh run --rm -u "$UID" --entrypoint "" dsm-api \
  pytest tests/unit_tests tests/validation

# Integration script provisions/migrates its test DB; arguments pass to pytest
./data-source-management/run_integration_tests.sh
./data-source-management/run_integration_tests.sh -k 'focused_expression'
```

- Frontend `npm test` deliberately exits successfully without running tests. `npm run format` writes files; it is not a check.
- Plain API `pytest` also collects `tests/integration_tests/`; do not use it as a unit-only shortcut.
- The integration script always stops and removes `dsm-api-test-db` on exit, even if that container existed before the run. Integration create/update paths also publish to MQTT.

## Alembic

```bash
./data-source-management/api/create_alembic_migration.sh <slug>
```

- Autogeneration uses the database configured for `dsm-api`, which must be reachable and current. Every API startup runs `alembic upgrade head` before Uvicorn and fails if migration fails.
- Import new SQLModel tables from `api/app/models/__init__.py`; Alembic targets global `SQLModel.metadata` and otherwise misses them.
- Inspect both `upgrade` and `downgrade` in every generated revision. Parser/API/ingest subtype additions also require updating model check constraints and `api/app/constants.py`; generated constraint changes commonly need hand edits.

## Environment and API Conventions

- Add API settings to `api/app/config.py::Settings` and consume the module-level `settings`; settings and the database engine are initialized at import time, so tests must install environment overrides before importing app modules.
- A frontend environment variable needs both a fallback/build mapping in `frontend/app/quasar.config.ts` and its placeholder in `frontend/docker/generic-image/entrypoint.sh`.
- Generic frontend images receive placeholder names such as `ENV_API_BASE_URL_PLACEHOLDER`; original names such as `API_BASE_URL` are build/dev inputs. An unset runtime placeholder is replaced with an empty string.
- Router inclusion order in `api/app/main.py` controls OpenAPI section order; keep router imports and `app.include_router()` calls aligned.
- Permission groups come from `eduperson_entitlement` values shaped as `a:a:a:group:<VO Name>:<Group Name>#`; accepted VO names are restricted by `ALLOWED_VOS`.
