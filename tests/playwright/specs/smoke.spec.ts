import { expect, test } from "@playwright/test";

const frontendPath =
  process.env.TIMEIO_FRONTEND_PATH ?? "/data-source-management/";

test("frontend exposes a login entry point @smoke", async ({ page }) => {
  await page.goto(frontendPath);

  const loginControls = page
    .getByRole("link", { name: /log\s*in|login|sign\s*in|anmelden/i })
    .or(page.getByRole("button", { name: /log\s*in|login|sign\s*in|anmelden/i }))
    .or(page.getByLabel(/username|user name|benutzer|login/i))
    .or(page.locator('input[name="username"], input[type="password"]'));

  await expect(loginControls.first()).toBeVisible();
});
