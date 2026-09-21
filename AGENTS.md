# Repository Instructions

## Sources of Truth

- This repository integrates TSM services; `docker-compose.yml` is the authoritative service graph, while most application images come from other repositories.
- Use `./dc.sh` and `./dc-with-dev.sh` instead of spelling out Compose files. Several root README examples still use legacy `docker-compose`, removed components, or obsolete sibling-repository mounts; verify operational guidance against scripts and Compose.
- `src/` contains this repository's Python workers and `timeio` package. `data-source-management/` contains the in-tree FastAPI and Quasar/Vue applications and has additional scoped instructions in `data-source-management/AGENTS.md`.
- Shared/public PostgreSQL changes use `flyway/migrations/public/`; the DSM API database has a separate Alembic history under `data-source-management/api/app/alembic/versions/`.
- The Kubernetes/Helm deployment of the same services lives in-tree under `helm/timeio/` (an umbrella chart with per-service subcharts). It was merged in from the former `ufz-tsm/helm-deployment` repo; the GitOps wrapper (`ufz-tsm/ufz-deployment`) remains a separate repo and consumes the published chart.

## Compose Workflow

Run these from the repository root:

```bash
cp .env.example .env                 # first setup only; .env is ignored
./dc.sh config --quiet               # validate interpolation before starting
./up.sh
./dc.sh ps
./dc.sh logs flyway                  # Flyway is a one-shot startup dependency
./down.sh
```

For source-mounted development, create the ignored override only if it is absent, then consistently use the dev wrappers:

```bash
cp docker-compose-dev.example.yml docker-compose-dev.yml
./dc-with-dev.sh config --quiet
./up-with-dev.sh
./down-with-dev.sh
```

- Startup ordering is intentional: `init`, PostgreSQL health, and Flyway precede dependent APIs and workers. Preserve `depends_on` conditions when changing service wiring.
- DSM changes publish `frontend_thing_update`; `worker-thing-setup` provisions PostgreSQL, MinIO, MQTT, Grafana, FROST context, and cron state. File/MQTT ingestion writes through the DB API, then `data_parsed` triggers QA/QC.
- The `init` container generates ignored certificates, keys, volume state, and `cron/crontab.txt`, and can change permissions on mounted configuration directories.

## Helm Chart

- The chart is at `helm/timeio/` (chart definition `helm/timeio/Chart.yaml`, subcharts under `helm/timeio/charts/`). Built dependency archives (`**/*.tgz`) and `Chart.lock` are gitignored via `helm/.gitignore`; CI regenerates them with `helm dependency build`.
- Validate locally without a cluster:

```bash
helm lint helm/timeio
helm dependency build helm/timeio     # pulls the postgres OCI dependency
helm template helm/timeio > /dev/null
```

- CI lives in `.gitlab/ci/09-helm-chart.gitlab-ci.yml` and runs **only when `helm/**` changes**, independently of the Docker image pipeline: branch pushes lint + template; a push to `main` enforces a **new** `Chart.yaml` `version:` (the pipeline hard-fails if that version already exists in the OCI registry), then packages, pushes (classic + OCI to `$CI_REGISTRY_IMAGE/charts`), and triggers the `ufz-tsm/ufz-deployment` chart promotion to the web-intern-TEST wrapper. **Bump `helm/timeio/Chart.yaml` `version:` in any MR that changes the chart**, or the post-merge pipeline fails.
- Chart history is in `helm/timeio/CHANGELOG.md`.
- TEMPORARY DUPLICATION: the chart currently vendors its own copies of assets that also live at the repo root and have drifted — most notably Flyway migrations (`helm/timeio/charts/flyway/conf/migrations/` vs `flyway/migrations/public/`), plus mosquitto/keycloak/cron/nginx config. Until these are unified to a single source (tracked follow-up), a change to one side must be mirrored to the other.

## Verification

Root Python CI uses Python 3.13 and runs only the `test_timeio` suite:

```bash
python3 -m pip install -r src/requirements.txt pytest black
black --check src/ tests/ data-source-management/api/app/
python3 -m pytest tests/test_timeio
python3 -m pytest tests/test_timeio/test_parser/test_csv.py  # focused file
```

- `tests/test_scripts/` is useful but not included in the CI Python-test job. `tests/test_deployment/` requires `.env` and a live, provisioned stack and may connect to PostgreSQL during collection.
- Validate environment key sets without exposing values using `python3 compare_dotenv_files.py .env .env.example`; CI checks `.env.example` against `releases/release.env` the same way.

## Migration and Runtime Traps

- Flyway starts with `repair migrate` and `baselineOnMigrate=true`. Never edit an applied SQL migration; add the next versioned migration and inspect `./dc.sh logs flyway` after startup.
- DSM API startup runs `alembic upgrade head` after Flyway. Follow the scoped DSM instructions for generating and testing Alembic revisions.
- Mosquitto creates its password database only when absent. Changing MQTT credentials in `.env` does not update existing password state under `data/` and can break health checks.
- Generated Tomcat/FROST context XML contains decrypted database credentials. Do not print or commit generated context or ignored environment/data files.
- Production deployment layers `releases/release.env` after the deployment `.env`, so release-file values win when keys overlap.
