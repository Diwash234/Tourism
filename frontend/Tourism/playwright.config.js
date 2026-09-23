import { defineConfig, devices } from "@playwright/test"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { browserLaunchOptions } from "./e2e/chromium.js"

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..")
const launchOptions = await browserLaunchOptions()

export default defineConfig({
  testDir: "./e2e",
  testIgnore: ["**/chromium.js", "**/helpers.js"],
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
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
      use: { ...devices["Desktop Chrome"] },
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
