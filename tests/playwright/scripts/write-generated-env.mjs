import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const outputPath = resolve(process.env.TIMEIO_GENERATED_ENV ?? ".env.generated");

if (existsSync(outputPath) && process.env.TIMEIO_GENERATED_ENV_FORCE !== "1") {
  throw new Error(
    `${outputPath} already exists; set TIMEIO_GENERATED_ENV_FORCE=1 to replace it.`,
  );
}

const suffix = randomBytes(4).toString("hex");
const username = process.env.TIMEIO_GENERATED_USERNAME ?? `timeio-ci-${suffix}`;
const password =
  process.env.TIMEIO_GENERATED_PASSWORD ?? randomBytes(24).toString("base64url");
const baseURL =
  process.env.TIMEIO_BASE_URL ?? "https://timeio.web-intern-stage.app.ufz.de";
const frontendPath =
  process.env.TIMEIO_FRONTEND_PATH ?? "/data-source-management/";

mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(
  outputPath,
  [
    "# Generated local Playwright environment. Do not commit.",
    `TIMEIO_BASE_URL=${baseURL}`,
    `TIMEIO_FRONTEND_PATH=${frontendPath}`,
    `TIMEIO_USERNAME=${username}`,
    `TIMEIO_PASSWORD=${password}`,
    "",
  ].join("\n"),
  { mode: 0o600 },
);

console.log(`Wrote ${outputPath}`);
