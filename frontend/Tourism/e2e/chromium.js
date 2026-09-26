import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { execFileSync } from "node:child_process"
import { createRequire } from "node:module"
import path from "node:path"
import zlib from "node:zlib"
import { chromium as playwrightChromium } from "@playwright/test"

// Browser selection for the e2e suite.
//
// 1. PLAYWRIGHT_CHROMIUM=/path/to/chrome  -> explicit override.
// 2. Playwright's own bundled Chromium (`npx playwright install chromium`,
//    which CI runs)                       -> Playwright defaults, no extra flags.
// 3. Otherwise (sandboxes without the Playwright download) fall back to the
//    @sparticuz/chromium binary.
//
// @sparticuz/chromium's default args are tuned for AWS Lambda and include
// `--single-process`, `--no-zygote` and `--headless='shell'`. Applied to a
// desktop Chrome (GitHub's runners ship /usr/bin/google-chrome) they make
// every `browser.newPage()` hang ("Test timeout ... while setting up page"),
// and even with the Lambda binary `--single-process` kills the browser as
// soon as a second page/context is opened. We therefore never pass those
// flags to anything but the Lambda binary, and strip `--single-process`
// even there.

const BASE_ARGS = ["--no-sandbox", "--disable-dev-shm-usage"]
const LAMBDA_ONLY_FLAGS = new Set(["--single-process", "--no-zygote"])

function bundledPlaywrightChromium() {
  try {
    const p = playwrightChromium.executablePath()
    return p && existsSync(p) ? p : null
  } catch {
    return null
  }
}

// The Lambda binary links against NSS/NSPR, which slim containers often lack.
// @sparticuz/chromium ships them in al2023.tar.br; unpack once to /tmp.
function sparticuzLibDir() {
  const libDir = "/tmp/al2023/lib"
  if (existsSync(path.join(libDir, "libnss3.so"))) return libDir
  try {
    const require = createRequire(import.meta.url)
    // package.json isn't in the package's "exports"; resolve the entry
    // (build/index.js) and walk up to the package root.
    const pkgDir = path.resolve(path.dirname(require.resolve("@sparticuz/chromium")), "..")
    const archive = path.join(pkgDir, "bin", "al2023.tar.br")
    if (!existsSync(archive)) return null
    mkdirSync("/tmp/al2023", { recursive: true })
    const tarPath = "/tmp/al2023/al2023.tar"
    writeFileSync(tarPath, zlib.brotliDecompressSync(readFileSync(archive)))
    execFileSync("tar", ["-xf", tarPath, "-C", "/tmp/al2023"])
    return existsSync(path.join(libDir, "libnss3.so")) ? libDir : null
  } catch {
    return null
  }
}

export async function browserLaunchOptions() {
  if (process.env.PLAYWRIGHT_CHROMIUM) {
    return { executablePath: process.env.PLAYWRIGHT_CHROMIUM, args: BASE_ARGS }
  }

  if (bundledPlaywrightChromium()) {
    return { args: BASE_ARGS }
  }

  const localChrome = [
    process.env.CHROMIUM_PATH,
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
  ].find((p) => p && existsSync(p))
  if (localChrome) {
    return { executablePath: localChrome, args: BASE_ARGS }
  }

  try {
    const sparticuz = (await import("@sparticuz/chromium")).default
    const executablePath = existsSync("/tmp/chromium") ? "/tmp/chromium" : await sparticuz.executablePath()
    const args = [
      ...sparticuz.args.filter((a) => !LAMBDA_ONLY_FLAGS.has(a)),
      "--disable-dev-shm-usage",
    ]
    const libDir = sparticuzLibDir()
    const env = libDir
      ? { ...process.env, LD_LIBRARY_PATH: [libDir, process.env.LD_LIBRARY_PATH].filter(Boolean).join(":") }
      : undefined
    return env ? { executablePath, args, env } : { executablePath, args }
  } catch {
    return { args: BASE_ARGS }
  }
}
