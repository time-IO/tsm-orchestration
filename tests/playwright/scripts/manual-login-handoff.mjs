import { chromium } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config({ quiet: true });

const baseURL =
  process.env.TIMEIO_BASE_URL ?? "https://timeio.web-intern-stage.app.ufz.de";
const frontendPath =
  process.env.TIMEIO_FRONTEND_PATH ?? "/data-source-management/";
const holdMs = Number.parseInt(process.env.TIMEIO_MANUAL_HOLD_MS ?? "", 10);

const browser = await chromium.launch({
  headless: false,
  slowMo: Number.parseInt(process.env.TIMEIO_SLOWMO_MS ?? "50", 10),
});

const context = await browser.newContext();
const page = await context.newPage();
await page.goto(new URL(frontendPath, baseURL).toString());

const loginControl = page
  .getByRole("link", { name: /log\s*in|login|sign\s*in|anmelden/i })
  .or(page.getByRole("button", { name: /log\s*in|login|sign\s*in|anmelden/i }))
  .or(page.getByLabel(/username|user name|benutzer|login/i))
  .or(page.locator('input[name="username"], input[type="password"]'))
  .first();

await loginControl.waitFor({ state: "visible", timeout: 10_000 });
await loginControl.evaluate((element) => {
  element.scrollIntoView({ block: "center", inline: "center" });
  element.style.outline = "4px solid #d97706";
  element.style.outlineOffset = "4px";
});
await loginControl.focus();

console.log(`Opened ${page.url()}`);
console.log("The login control is highlighted. Continue manually in the browser.");
console.log("Press Ctrl+C in this terminal when you are done.");

if (Number.isFinite(holdMs) && holdMs > 0) {
  await page.waitForTimeout(holdMs);
} else {
  await new Promise((resolve) => {
    process.once("SIGINT", resolve);
    process.once("SIGTERM", resolve);
  });
}

await browser.close();
