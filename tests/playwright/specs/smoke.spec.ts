import { expect, test } from "@playwright/test";

const frontendPath =
  process.env.TIMEIO_FRONTEND_PATH ?? "/data-source-management/";

test("frontend exposes a login entry point @smoke", async ({ page }) => {
  const response = await page.goto(frontendPath, {
    waitUntil: "domcontentloaded",
  });

  expect(
    response,
    "frontend navigation should return an HTTP response",
  ).not.toBeNull();
  expect(
    response!.ok(),
    `frontend navigation returned ${response!.status()} ${response!.statusText()}`,
  ).toBeTruthy();

  const loginControls = page
    .getByRole("link", { name: /log\s*in|login|sign\s*in|anmelden/i })
    .or(page.getByRole("button", { name: /log\s*in|login|sign\s*in|anmelden/i }))
    .or(page.getByLabel(/username|user name|benutzer|login/i))
    .or(page.locator('input[name="username"], input[type="password"]'));

  await expect(loginControls.first()).toBeVisible();
});
