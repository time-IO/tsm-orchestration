# TimeIO Playwright POC

This is a first browser-test POC for the composed TimeIO deployment.

The default target is web-intern-stage:

```bash
cd tests/playwright
npm install
npm test
```

Run only the no-secret smoke tests:

```bash
npm run test:smoke
```

Run only credential-gated tests:

```bash
npm run test:auth
```

The login/logout test follows TimeIO's browser OIDC redirect: it opens the
frontend, signs in at the configured provider, returns through
`/login-callback`, and logs out. Automate it only against a controlled realm,
such as the repository's local development Keycloak. It is not evidence for
Helmholtz AAI, Stage, or production SSO; that policy is tracked separately in
OpenProject #21219.

For a manual headed login handoff:

```bash
npm run manual:login
```

This opens Chromium at the DSM frontend, highlights the login control, and
waits so you can continue manually in the browser. Press Ctrl+C in the terminal
to close the browser when finished.

Useful environment variables:

- `TIMEIO_BASE_URL`: deployment root, defaults to
  `https://timeio.web-intern-stage.app.ufz.de`.
- `TIMEIO_FRONTEND_PATH`: frontend path, defaults to
  `/data-source-management/`.
- `TIMEIO_USERNAME` and `TIMEIO_PASSWORD`: optional credentials for the form
  shown by a controlled OIDC provider.
- `TIMEIO_STORAGE_STATE`: optional Playwright auth state path, for example
  `.auth/timeio.json`.
- `TIMEIO_SLOWMO_MS`: optional delay between manual browser actions, defaults
  to `50`.
- `TIMEIO_GENERATED_ENV`: optional output path for `npm run env:generated`,
  defaults to `.env.generated`.

For throwaway local or CI deployments, generate a local env file:

```bash
npm run env:generated
```

The generated file contains a random username/password pair for an environment
that is provisioned with matching credentials. Creating the app user is still a
deployment responsibility; Playwright only consumes the values.

## Controlled-Keycloak CI

The `playwright-login` job starts the branch-built Compose stack on a `dind`
runner, replaces the production Keycloak realm import with the development
realm, and runs the `@auth` tests from a one-shot Playwright container on the
same Compose network. The Playwright service shares the proxy service's network
namespace, so browser `http://localhost` reaches nginx while remaining a
trustworthy loopback context. This makes Web Crypto available to
`oidc-client-ts` for PKCE without weakening normal browser security settings.
No deployed TimeIO environment is contacted.

The job uses the development realm's throwaway `user1`/`password` account.
These are not Stage or production credentials. Like the other Playwright jobs,
the job runs on branch pushes only: it is disabled for tags, merge-request
pipelines, and `main`. The controlled auth job disables traces, videos,
screenshots, and the HTML report and uploads no browser or service artifacts;
OIDC codes, tokens, and sessions must not leave the ephemeral runner.

To reproduce the controlled stack locally from the repository root, use a
dedicated Compose project so its volumes can be removed without touching a
normal development stack:

```bash
test -f .env || cp .env.example .env
AUTH_COMPOSE=(docker compose -p timeio-auth-local \
  -f docker-compose.yml -f docker-compose-ci-e2e.yml)
"${AUTH_COMPOSE[@]}" build dsm-frontend
"${AUTH_COMPOSE[@]}" up -d --wait --wait-timeout 300 \
  proxy keycloak dsm-frontend dsm-api
"${AUTH_COMPOSE[@]}" run --rm playwright
"${AUTH_COMPOSE[@]}" down --volumes --remove-orphans
```

The non-frontend images must be available from their configured registries.
The final command removes only the `timeio-auth-local` project's containers,
network, and volumes.

For SSO or other interactive login flows, run headed once and save storage
state manually under `.auth/`. Do not commit `.auth/`, traces, HAR files, or
other auth-bearing artifacts. Do not commit `.env.generated`.
