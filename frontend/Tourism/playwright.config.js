import { defineConfig, devices } from "@playwright/test"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { browserLaunchOptions } from "./e2e/chromium.js"

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..")
const launchOptions = await browserLaunchOptions()

export default defineConfig({
  testDir: "./e2e",
  testIgnore: ["**/chromium.js", "**/helpers.js"],
  // Each test drives its own page and calls setViewportSize() itself, so there
  // is no shared state between them. Running all 798 checks (266 route x
  // viewport combinations across three device projects) serially at workers: 1
  // took 1475s and was killed by the job timeout before finishing.
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // GitHub-hosted runners have 2 cores; two workers roughly halves the wall
  // clock without oversubscribing. Unset locally so Playwright picks its own
  // default.
  workers: process.env.CI ? 2 : undefined,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    launchOptions,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], isMobile: false },
    },
    // NOTE: layout.spec.js force-sets the viewport per test, and its WIDTHS
    // matrix already covers 375px (Pixel 7) and 768px (tablet). Running that
    // spec under these projects would triple the runtime without measuring
    // anything new, because horizontal overflow and text overlap do not depend
    // on isMobile. The workflow therefore passes --project=chromium for that
    // one spec; these projects still apply to the rest of the e2e suite.
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 7"] },
    },
    {
      name: "tablet",
      use: { viewport: { width: 768, height: 1024 }, isMobile: true },
    },
  ],
  webServer: [
    {
      command: "bash scripts/e2e-backend.sh",
      cwd: root,
      url: "http://127.0.0.1:8000/api/v1/config/public/",
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
    },
    {
      command: "npm run dev -- --host 0.0.0.0 --port 5173",
      cwd: path.dirname(fileURLToPath(import.meta.url)),
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
})
