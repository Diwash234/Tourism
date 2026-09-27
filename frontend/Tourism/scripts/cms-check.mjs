/* global document */
// End-to-end CMS coverage check: edits pages the way an admin does (through
// the admin CMS API the dashboard uses), publishes, then loads the real pages
// in Chromium and asserts the published content and SEO appear.
//
//   BASE_URL=http://127.0.0.1:5173 API_URL=http://127.0.0.1:8000 \
//   CMS_ADMIN_EMAIL=... CMS_ADMIN_PASSWORD=... node scripts/cms-check.mjs
//
// It writes to the CMS, so only run it against a disposable/dev database.
import { chromium } from "@playwright/test"
import { browserLaunchOptions } from "../e2e/chromium.js"

const BASE = process.env.BASE_URL || "http://127.0.0.1:5173"
const API = `${process.env.API_URL || "http://127.0.0.1:8000"}/api/v1`
const email = process.env.CMS_ADMIN_EMAIL
const password = process.env.CMS_ADMIN_PASSWORD
if (!email || !password) throw new Error("CMS_ADMIN_EMAIL and CMS_ADMIN_PASSWORD are required")

const results = []
const record = (name, ok, detail = "") => { results.push({ name, ok, detail }); console.log(`${ok ? "PASS" : "FAIL"} ${name}${detail ? ` - ${detail}` : ""}`) }

const login = await fetch(`${API}/auth/login/`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email, password }) })
const { access } = await login.json()
const auth = { Authorization: `Bearer ${access}`, "content-type": "application/json" }
const cms = async (method, params, body) => {
  const query = method === "GET" ? `?${new URLSearchParams(params)}` : ""
  const response = await fetch(`${API}/admin/cms/${query}`, { method, headers: auth, body: body ? JSON.stringify(body) : undefined })
  if (!response.ok) throw new Error(`${method} ${JSON.stringify(params || body)} -> ${response.status} ${await response.text()}`)
  return response.json()
}

const pages = (await cms("GET", { resource: "pages" })).results
const byKey = Object.fromEntries(pages.map((page) => [page.key, page]))

// Publish a visible intro section with a unique marker on each page.
const publishIntro = async (key) => {
  const page = byKey[key]
  if (!page) throw new Error(`no ManagedPage with key ${key}`)
  const sections = (await cms("GET", { resource: "sections", page_id: page.id })).results
  const intro = sections.find((section) => section.key === "intro") || sections[0]
  const marker = `CMS check ${key}`
  let id = intro?.id
  if (id) await cms("PATCH", null, { resource: "sections", id, title: marker, body: `Edited in the CMS for ${key}.`, is_visible: true })
  else id = (await cms("POST", null, { resource: "sections", page_id: page.id, key: "intro", title: marker, body: `Edited in the CMS for ${key}.`, is_visible: true })).id
  await cms("PATCH", null, { resource: "sections", id, action: "publish" })
  return marker
}

// [page key, URL, needs sign-in]
const TARGETS = [
  ["before-you-travel", "/before-you-travel"], ["cookie-policy", "/cookie-policy"], ["privacy-policy", "/privacy-policy"],
  ["terms-of-service", "/terms-of-service"], ["data-deletion", "/data-deletion"], ["districts", "/districts"],
  ["district-detail", "/districts/Kaski"], ["search", "/search"], ["discover", "/discover"], ["decide", "/decide"],
  ["distances", "/distances"], ["trip-status", "/trip"], ["unsubscribe", "/unsubscribe"], ["auth-recovery", "/forgot-password"],
  ["auth-verify-email", "/verify-email"], ["auth-reset-password", "/reset-password"], ["portal-login", "/portal"],
  ["not-found", "/this-page-does-not-exist"], ["auth-login-user", "/login/user"],
  ["admin-console", "/admin", true], ["admin-tasks", "/admin/tasks", true], ["admin-diagnostics", "/admin/diagnostics", true],
]
const markers = {}
for (const [key] of TARGETS) markers[key] = await publishIntro(key)

// SEO edit on a page that used to hard-code its metadata.
await cms("PATCH", null, { resource: "pages", id: byKey.discover.id, seo_title: "CMS SEO check discover", meta_description: "CMS meta description check for discover." })
await cms("PATCH", null, { resource: "pages", id: byKey.discover.id, action: "publish" })

const browser = await chromium.launch(await browserLaunchOptions())
const context = await browser.newContext()
const page = await context.newPage()
const visible = async (text) => page.getByText(text, { exact: true }).first().waitFor({ state: "visible", timeout: 15000 }).then(() => true, () => false)

for (const [key, url] of TARGETS.filter((target) => !target[2])) {
  await page.goto(`${BASE}${url}`, { waitUntil: "domcontentloaded" })
  record(`${url} shows CMS content (${key})`, await visible(markers[key]))
}

// Alias routes are separately editable: /login/user content must not leak to /login.
await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" })
await page.getByRole("heading").first().waitFor({ timeout: 15000 })
await page.waitForTimeout(1500)
record("/login does not show the /login/user alias content", !(await page.getByText(markers["auth-login-user"], { exact: true }).count()))

// A real 404 still shows the 404 page (plus its CMS area).
await page.goto(`${BASE}/this-page-does-not-exist`, { waitUntil: "domcontentloaded" })
record("unknown URL still renders the 404 page", await page.getByRole("heading", { level: 1 }).first().textContent({ timeout: 15000 }).then((t) => /couldn.t find that page/i.test(t || ""), () => false))

// Admin-created CMS page on a custom route and via /page/:slug.
const custom = pages.find((item) => item.route && !item.route.includes(":") && item.key === "best-winter-destinations")
if (custom) {
  for (const url of [custom.route, `/page/${custom.key}`]) {
    await page.goto(`${BASE}${url}`, { waitUntil: "domcontentloaded" })
    const h1 = await page.getByRole("heading", { level: 1 }).first().textContent({ timeout: 15000 }).catch(() => "")
    record(`${url} renders the admin-created CMS page`, h1.trim() === custom.title, `h1="${h1.trim()}"`)
  }
}
await page.goto(`${BASE}/page/no-such-cms-page`, { waitUntil: "domcontentloaded" })
record("/page/<unknown> renders 404", await page.getByRole("heading", { level: 1 }).first().textContent({ timeout: 15000 }).then((t) => /couldn.t find that page/i.test(t || ""), () => false))

// SEO from the CMS record.
await page.goto(`${BASE}/discover`, { waitUntil: "domcontentloaded" })
await page.waitForFunction(() => document.title.includes("CMS SEO check"), null, { timeout: 15000 }).catch(() => {})
const description = await page.locator('meta[name="description"]').getAttribute("content").catch(() => "")
record("/discover title comes from the CMS record", (await page.title()).includes("CMS SEO check discover"), await page.title())
record("/discover meta description comes from the CMS record", description === "CMS meta description check for discover.", description)

// Signed-in consoles.
await page.goto(`${BASE}/admin/login`, { waitUntil: "domcontentloaded" })
await page.locator('input[type="email"], input[name="email"]').first().fill(email)
await page.locator('input[type="password"]').first().fill(password)
await page.locator('form button[type="submit"]').first().click()
await page.waitForURL((url) => !url.pathname.includes("login"), { timeout: 20000 }).catch(() => {})
for (const [key, url] of TARGETS.filter((target) => target[2])) {
  await page.goto(`${BASE}${url}`, { waitUntil: "domcontentloaded" })
  record(`${url} shows CMS content (${key})`, await visible(markers[key]))
}

await browser.close()
const failed = results.filter((result) => !result.ok)
console.log(`\n${results.length - failed.length}/${results.length} passed`)
process.exit(failed.length ? 1 : 0)
