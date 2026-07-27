import { expect, test } from "@playwright/test";

const username = process.env.TIMEIO_USERNAME;
const password = process.env.TIMEIO_PASSWORD;
const authState = process.env.TIMEIO_STORAGE_STATE;

const frontendPath =
  process.env.TIMEIO_FRONTEND_PATH ?? "/data-source-management/";

test("user can log in and log out with form credentials @auth", async ({ page }) => {
  test.skip(
    !username || !password,
    "Set TIMEIO_USERNAME and TIMEIO_PASSWORD for a form-login run.",
  );

  await page.goto(frontendPath);
  await page.getByLabel(/username|user name|benutzer|login/i).fill(username);
  await page.getByLabel(/password|passwort/i).fill(password);
  await page
    .getByRole("button", { name: /log\s*in|login|sign\s*in|anmelden/i })
    .click();

  await expect(
    page.getByRole("link", { name: /log\s*out|logout|abmelden/i }).or(
      page.getByRole("button", { name: /log\s*out|logout|abmelden/i }),
    ),
  ).toBeVisible();

  await page
    .getByRole("link", { name: /log\s*out|logout|abmelden/i })
    .or(page.getByRole("button", { name: /log\s*out|logout|abmelden/i }))
    .click();

  await expect(
    page.getByRole("link", { name: /log\s*in|login|sign\s*in|anmelden/i }).or(
      page.getByRole("button", { name: /log\s*in|login|sign\s*in|anmelden/i }),
    ),
  ).toBeVisible();
});

test("authenticated session exposes a logout entry point @auth", async ({ browser }) => {
  test.skip(!authState, "Set TIMEIO_STORAGE_STATE=.auth/timeio.json after a headed login.");

  const context = await browser.newContext({ storageState: authState });
  const page = await context.newPage();
  await page.goto(frontendPath);

  await expect(
    page.getByRole("link", { name: /log\s*out|logout|abmelden/i }).or(
      page.getByRole("button", { name: /log\s*out|logout|abmelden/i }),
    ),
  ).toBeVisible();

  await context.close();
});
