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

The credential-gated login/logout test follows TimeIO's real browser OIDC
redirect: it clicks Login in the frontend, signs in at the configured provider,
returns through `/login-callback`, and then logs out. Use it automatically only
against a controlled realm, such as the repository's local development
Keycloak. It is not evidence for Helmholtz AAI, Stage, or production SSO.
Stage and production SSO policy and coverage are tracked separately under
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
  shown by the configured OIDC provider. Supply only a controlled test identity.
- `TIMEIO_STORAGE_STATE`: optional Playwright auth state path, for example
  `.auth/timeio.json`.
- `TIMEIO_SLOWMO_MS`: optional delay between manual browser actions, defaults
  to `50`.
- `TIMEIO_BROWSER_HOST_RESOLVER_RULES`: optional Chromium host mapping for a
  local test-only OIDC hostname, for example `MAP timeio.test 127.0.0.1`.
- `TIMEIO_GENERATED_ENV`: optional output path for `npm run env:generated`,
  defaults to `.env.generated`.

For throwaway local or CI deployments, generate a local env file:

```bash
npm run env:generated
```

The generated file contains a random username/password pair for an environment
that is provisioned with matching credentials. Creating the app user is still a
deployment responsibility; Playwright only consumes the values.

For local development, the repository already provides that controlled
environment declaratively: `docker-compose.yml` imports a Keycloak realm, and
`docker-compose-dev.example.yml` replaces it with the development realm that
contains local users and the `timeIO-client` configuration. Start the local
stack following the repository README, then provide the selected local user's
credentials through ignored environment variables when invoking Playwright.

```bash
cd tests/playwright
TIMEIO_BASE_URL=http://localhost \
TIMEIO_USERNAME='<controlled-local-user>' \
TIMEIO_PASSWORD='<controlled-local-password>' \
npm run test:auth
```

The placeholder values above are deliberately not repository configuration:
select a local development identity without adding its credentials to a file or
CI variable.

## Controlled-Keycloak CI

The `playwright-login` job starts the branch-built Compose stack on a `dind`
runner, replaces the production Keycloak realm import with the development
realm, and runs the credential-gated `@auth` tests from a one-shot Playwright
container on the same Compose network. It pins the stack to the `proxy`
hostname so the OIDC redirect chain stays internal to the local test
environment.

The credentials used there are the local development realm's throwaway
`user1`/`password` account. They are not Stage or production credentials, and
the job is deliberately disabled for merge-request pipelines and `main`.

For SSO or other interactive login flows, run headed once and save storage
state manually under `.auth/`. Do not commit `.auth/`, traces, HAR files, or
other auth-bearing artifacts. Do not commit `.env.generated`.
