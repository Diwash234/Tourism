import { existsSync } from "node:fs"

const localChrome = [
  process.env.CHROMIUM_PATH,
  "/tmp/chromium",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/usr/bin/google-chrome",
].find((path) => path && existsSync(path))

export async function browserLaunchOptions() {
  if (process.env.PLAYWRIGHT_CHROMIUM) {
    return { executablePath: process.env.PLAYWRIGHT_CHROMIUM, args: ["--no-sandbox", "--disable-dev-shm-usage"] }
  }
  try {
    const chromium = (await import("@sparticuz/chromium")).default
    const executablePath = localChrome || await chromium.executablePath()
    return {
      executablePath,
      args: [...chromium.args, "--disable-dev-shm-usage"],
    }
  } catch {
    if (localChrome) {
      return { executablePath: localChrome, args: ["--no-sandbox", "--disable-dev-shm-usage"] }
    }
    return { args: ["--no-sandbox", "--disable-dev-shm-usage"] }
  }
}
