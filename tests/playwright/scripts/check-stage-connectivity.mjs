import dns from "node:dns/promises";
import http from "node:http";
import https from "node:https";
import { performance } from "node:perf_hooks";

const baseURL =
  process.env.TIMEIO_BASE_URL ?? "https://timeio.web-intern-stage.app.ufz.de";
const frontendPath =
  process.env.TIMEIO_FRONTEND_PATH ?? "/data-source-management/";
const timeoutMs = Number.parseInt(
  process.env.TIMEIO_CONNECTIVITY_TIMEOUT_MS ?? "15000",
  10,
);
const maxRedirects = 5;
const target = new URL(frontendPath, baseURL);

const lookupStarted = performance.now();
const addresses = await dns.lookup(target.hostname, { all: true });
console.log(
  `DNS ${target.hostname}: ${addresses
    .map((address) => address.address)
    .join(", ")} (${Math.round(performance.now() - lookupStarted)} ms)`,
);

const request = (url, redirects = []) =>
  new Promise((resolve, reject) => {
    const started = performance.now();
    const client = url.protocol === "https:" ? https : http;
    const req = client.request(
      url,
      {
        method: "GET",
        timeout: timeoutMs,
        headers: {
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "User-Agent": "timeio-playwright-connectivity-check",
        },
      },
      (res) => {
        const statusCode = res.statusCode ?? 0;
        const location = res.headers.location;
        const elapsedMs = Math.round(performance.now() - started);

        if (
          location &&
          statusCode >= 300 &&
          statusCode < 400 &&
          redirects.length < maxRedirects
        ) {
          res.resume();
          const nextUrl = new URL(location, url);
          console.log(`HTTP ${statusCode} redirect: ${url} -> ${nextUrl}`);
          resolve(request(nextUrl, [...redirects, url.toString()]));
          return;
        }

        let bytes = 0;
        res.on("data", (chunk) => {
          bytes += chunk.length;
        });
        res.on("end", () => {
          resolve({
            elapsedMs,
            finalUrl: url.toString(),
            statusCode,
            statusMessage: res.statusMessage,
            contentType: res.headers["content-type"] ?? "",
            bytes,
            redirects,
          });
        });
      },
    );

    req.on("timeout", () => {
      req.destroy(new Error(`Timed out after ${timeoutMs} ms`));
    });
    req.on("error", reject);
    req.end();
  });

const response = await request(target);
console.log(
  `HTTP ${response.statusCode} ${response.statusMessage} from ${response.finalUrl} ` +
    `(${response.elapsedMs} ms, ${response.bytes} bytes, ${response.contentType})`,
);

if (response.statusCode < 200 || response.statusCode >= 400) {
  throw new Error(
    `Stage frontend connectivity check failed with HTTP ${response.statusCode}`,
  );
}
