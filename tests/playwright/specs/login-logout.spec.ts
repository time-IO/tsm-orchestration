import { expect, test, type Page } from "@playwright/test";

const username = process.env.TIMEIO_USERNAME;
const password = process.env.TIMEIO_PASSWORD;
const authState = process.env.TIMEIO_STORAGE_STATE;

const frontendPath =
  process.env.TIMEIO_FRONTEND_PATH ?? "/data-source-management/";

const loginControlName = /log\s*in|login|sign\s*in|anmelden/i;
const logoutControlName = /log\s*out|logout|abmelden/i;

function loginControl(page: Page) {
  return page
    .getByRole("link", { name: loginControlName })
    .or(page.getByRole("button", { name: loginControlName }));
}

function logoutControl(page: Page) {
  return page.locator(".q-menu .q-item").filter({ hasText: logoutControlName });
}

function accountControl(page: Page) {
  return page.getByRole("button", { name: /account/i });
}

async function reachKeycloakLogin(page: Page) {
  await page.goto(frontendPath);

  const usernameField = page.locator("#username");
  if (await usernameField.isVisible({ timeout: 5_000 })) {
    return usernameField;
  }

  // TimeIO itself has no username/password form. Its Login control redirects
  // to the configured OIDC provider, where this test enters the credentials.
  await loginControl(page).click();
  await expect(page).toHaveURL(/\/protocol\/openid-connect\/auth(?:\?|$)/);

  await expect(usernameField).toBeVisible();
  return usernameField;
}

async function expectLoggedOut(page: Page) {
  const usernameField = page.locator("#username");
  if (await usernameField.isVisible({ timeout: 10_000 })) {
    return;
  }

  // Some IdP/logout configurations return to the anonymous app instead of the
  // login form. In that state Login is an entry in the account popover.
  await expect(accountControl(page)).toBeVisible();
  await accountControl(page).click();
  await expect(loginControl(page)).toBeVisible();
}

test("controlled origin provides Web Crypto for OIDC PKCE @auth", async ({
  page,
}) => {
  await page.goto(frontendPath);

  const capabilities = await page.evaluate(() => ({
    isSecureContext: window.isSecureContext,
    hasSubtleCrypto: typeof window.crypto?.subtle !== "undefined",
  }));

  expect(capabilities).toEqual({
    isSecureContext: true,
    hasSubtleCrypto: true,
  });
});

test("user can sign in through OIDC and log out with form credentials @auth", async ({
  page,
}) => {
  test.skip(
    !username || !password,
    "Set TIMEIO_USERNAME and TIMEIO_PASSWORD for a controlled OIDC form-login run.",
  );

  const usernameField = await reachKeycloakLogin(page);

  // The custom timeio-login theme renders bare inputs with placeholders and no
  // <label>, so locate the fields by id rather than by role/label.
  await usernameField.fill(username);
  await page.locator("#password").fill(password);

  // The callback marks the OIDC user as loaded before the asynchronous DSM
  // profile request completes. Observe /me/ before submitting so a broken
  // discovery/JWKS/userinfo backchannel cannot race past the menu assertions.
  const meResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "GET" &&
      new URL(response.url()).pathname ===
        "/data-source-management/api/me/",
  );
  await page
    .locator(
      "#kc-form-login button[type=submit], #kc-form-login input[type=submit]",
    )
    .click();

  // Success is defined by where the redirect chain lands: back on the app path,
  // no longer on the Keycloak login page. This is robust to the app's own markup,
  // which is the part most likely to drift.
  await page.waitForURL(
    (url) =>
      url.pathname.startsWith(frontendPath) &&
      !url.pathname.startsWith("/keycloak"),
  );
  await expect(page).not.toHaveURL(/\/keycloak\//);

  const authenticatedProfile = await meResponse;
  expect(authenticatedProfile.status()).toBe(200);

  await expect(accountControl(page)).toBeVisible();
  await accountControl(page).click();
  await expect(logoutControl(page)).toBeVisible();

  await logoutControl(page).click();
  await expectLoggedOut(page);
});

test("authenticated session exposes a logout entry point @auth", async ({
  browser,
}) => {
  test.skip(
    !authState,
    "Set TIMEIO_STORAGE_STATE=.auth/timeio.json after a headed login.",
  );

  const context = await browser.newContext({ storageState: authState });
  const page = await context.newPage();
  await page.goto(frontendPath);

  await expect(accountControl(page)).toBeVisible();
  await accountControl(page).click();
  await expect(logoutControl(page)).toBeVisible();

  await context.close();
});
