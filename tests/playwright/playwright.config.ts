import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";

dotenv.config({ quiet: true });

const baseURL =
  process.env.TIMEIO_BASE_URL ?? "https://timeio.web-intern-stage.app.ufz.de";
const controlledAuthCi = process.env.TIMEIO_CONTROLLED_AUTH_CI === "true";

export default defineConfig({
  testDir: "./specs",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    trace: controlledAuthCi ? "off" : "retain-on-failure",
    screenshot: controlledAuthCi ? "off" : "only-on-failure",
    video: controlledAuthCi ? "off" : "retain-on-failure",
  },
  reporter: controlledAuthCi
    ? [["list"]]
    : [["list"], ["html", { open: "never" }]],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
