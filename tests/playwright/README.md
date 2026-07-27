# TimeIO Playwright POC

This is a first browser-test POC for the composed TimeIO deployment.

The default target is web-intern-stage:

```bash
cd tests/playwright
npm install
npm test
```

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
- `TIMEIO_USERNAME` and `TIMEIO_PASSWORD`: optional form-login credentials.
- `TIMEIO_STORAGE_STATE`: optional Playwright auth state path, for example
  `.auth/timeio.json`.
- `TIMEIO_SLOWMO_MS`: optional delay between manual browser actions, defaults
  to `50`.

For SSO or other interactive login flows, run headed once and save storage
state manually under `.auth/`. Do not commit `.auth/`, traces, HAR files, or
other auth-bearing artifacts.
