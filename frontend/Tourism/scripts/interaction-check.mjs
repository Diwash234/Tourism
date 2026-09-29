// Rendered interaction checks for the release audit (run against the dev
// server + API). Verifies behaviour a static audit cannot see:
//   - cookie banner: equal-weight choices, nothing from YouTube/Vimeo before
//     consent, choice persists, footer "Cookie settings" reopens with focus
//   - mobile drawer: Escape closes it and focus returns to the toggle
//   - self-service account deletion through the real UI
//   - unsubscribe page: bad token error, neutral email reply
//   - auth forms: every input has a label, exactly one h1
// Usage: BASE_URL=http://localhost:5173 DELETE_EMAIL=... DELETE_PASSWORD=... node scripts/interaction-check.mjs
import { chromium } from "@playwright/test"
import { browserLaunchOptions } from "../e2e/chromium.js"

const BASE = process.env.BASE_URL || "http://localhost:5173"
const results = []
const check = (name, ok, detail = "") => { results.push({ name, ok: !!ok, detail }); console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? `  (${detail})` : ""}`) }

const browser = await chromium.launch(await browserLaunchOptions())

// 1. Cookie banner
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } })
  const videoHosts = []
  ctx.on("request", (r) => { if (/youtube|ytimg|vimeo/.test(r.url())) videoHosts.push(r.url()) })
  const page = await ctx.newPage()
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" })
  const banner = page.getByRole("region", { name: /cookies and embedded videos/i })
  check("banner shows on first visit", await banner.isVisible())
  const essential = banner.getByRole("button", { name: "Essential only" })
  const allow = banner.getByRole("button", { name: "Allow videos" })
  const style = (loc) => loc.evaluate((el) => { const c = getComputedStyle(el); const r = el.getBoundingClientRect(); return [c.backgroundColor, c.color, c.fontSize, c.fontWeight, Math.round(r.height), Math.round(r.width)].join("|") })
  const [sa, sb] = [await style(essential), await style(allow)]
  check("reject and accept are styled identically", sa === sb, `${sa} vs ${sb}`)
  check("no dismiss-means-accept close button", (await banner.getByRole("button").count()) === 2)
  check("no request to YouTube/Vimeo before consent", videoHosts.length === 0, videoHosts[0] || "")
  await essential.click()
  check("banner closes after a choice", !(await banner.isVisible()))
  const stored = await page.evaluate(() => localStorage.getItem("tourism_cookie_consent"))
  check("essential-only choice stored with media=false", stored && JSON.parse(stored).media === false, stored)
  await page.reload({ waitUntil: "networkidle" })
  check("choice persists across reload", !(await banner.isVisible()))
  await page.getByRole("button", { name: "Cookie settings" }).first().click()
  check("footer 'Cookie settings' reopens the banner", await banner.isVisible())
  const focused = await page.evaluate(() => document.activeElement?.textContent?.trim())
  check("focus moves into the reopened banner", focused === "Essential only", focused)
  await banner.getByRole("button", { name: "Allow videos" }).click()
  const stored2 = await page.evaluate(() => localStorage.getItem("tourism_cookie_consent"))
  check("changing the choice to allow is stored", JSON.parse(stored2).media === true)
  await ctx.close()
}

// 2. Mobile drawer
{
  const ctx = await browser.newContext({ viewport: { width: 375, height: 800 } })
  const page = await ctx.newPage()
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" })
  await page.evaluate(() => localStorage.setItem("tourism_cookie_consent", JSON.stringify({ media: false })))
  await page.reload({ waitUntil: "networkidle" })
  const toggle = page.locator('[aria-controls="sidebar-drawer"]').first()
  await toggle.click()
  check("menu toggle reports expanded", (await toggle.getAttribute("aria-expanded")) === "true")
  await page.keyboard.press("Escape")
  await page.waitForTimeout(400)
  check("Escape closes the mobile drawer", (await toggle.getAttribute("aria-expanded")) === "false")
  const back = await page.evaluate(() => document.activeElement?.getAttribute("aria-controls"))
  check("focus returns to the menu toggle", back === "sidebar-drawer", String(back))
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  check("no sideways scroll at 375px", overflow <= 0, `${overflow}px`)
  await ctx.close()
}

// 3. Auth forms: labels + single h1
for (const path of ["/login", "/register", "/forgot-password"]) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } })
  const page = await ctx.newPage()
  await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" })
  const info = await page.evaluate(() => {
    const unlabelled = [...document.querySelectorAll("main input:not([type=hidden]):not([type=checkbox]), main textarea, main select")]
      .filter((el) => el.offsetParent !== null)
      .filter((el) => !(el.labels && el.labels.length) && !el.getAttribute("aria-label") && !el.getAttribute("aria-labelledby"))
    return { h1: document.querySelectorAll("h1").length, unlabelled: unlabelled.map((e) => e.outerHTML.slice(0, 80)) }
  })
  check(`${path}: exactly one h1`, info.h1 === 1, String(info.h1))
  check(`${path}: every visible field has a label`, info.unlabelled.length === 0, info.unlabelled[0] || "")
  await ctx.close()
}

// 4. Unsubscribe
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } })
  const page = await ctx.newPage()
  await page.goto(`${BASE}/unsubscribe?token=not-a-real-token`, { waitUntil: "networkidle" })
  const alert = await page.getByRole("alert").first().textContent().catch(() => "")
  check("bad unsubscribe link shows an error and the email form", /not valid/i.test(alert) && (await page.getByLabel("Email address").isVisible()), alert)
  await page.getByLabel("Email address").fill("nobody-subscribed@example.org")
  await page.getByRole("button", { name: "Unsubscribe" }).click()
  const status = await page.getByText(/if that address was subscribed/i).first().textContent({ timeout: 8000 }).catch(() => "")
  check("email unsubscribe gives the neutral reply", /if that address was subscribed/i.test(status), status)
  await ctx.close()
}

// 5. Account deletion through the UI
if (process.env.DELETE_EMAIL && process.env.DELETE_PASSWORD) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } })
  const page = await ctx.newPage()
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" })
  await page.getByLabel("Email address").fill(process.env.DELETE_EMAIL)
  await page.getByLabel("Password", { exact: true }).fill(process.env.DELETE_PASSWORD)
  await page.locator('form button[type="submit"]').first().click()
  await page.waitForFunction(() => !!localStorage.getItem("access"), null, { timeout: 15000 }).catch(() => {})
  check("test user signed in", await page.evaluate(() => !!localStorage.getItem("access")))
  // Signed in, the page must stay signed in (regression: tokens were dropped).
  await page.goto(`${BASE}/settings`, { waitUntil: "networkidle" })
  const card = page.locator('section[aria-labelledby="privacy-data-title"]')
  const cardOk = await card.waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false)
  // Fresh context: close the first-visit banner so the reopen check is meaningful.
  const firstVisit = page.getByRole("button", { name: /essential only/i })
  if (await firstVisit.isVisible().catch(() => false)) await firstVisit.click()
  await page.getByRole("button", { name: /essential only/i }).waitFor({ state: "hidden", timeout: 3000 }).catch(() => {})
  const links = cardOk ? await card.locator("a").evaluateAll((as) => as.map((a) => a.getAttribute("href"))) : []
  check("settings privacy card shows policy + deletion links", cardOk && links.includes("/privacy-policy") && links.includes("/data-deletion"), links.join(","))
  check("still signed in on a protected page", await page.evaluate(() => !!localStorage.getItem("access")) && !(await page.getByText(/session has expired/i).isVisible().catch(() => false)))
  if (cardOk) {
    await card.getByRole("button", { name: "Cookie settings" }).click()
    check("settings card reopens the cookie choice", await page.getByRole("button", { name: /essential only/i }).isVisible({ timeout: 3000 }).catch(() => false))
    await page.getByRole("button", { name: /essential only/i }).click().catch(() => {})
  }
  await page.goto(`${BASE}/data-deletion`, { waitUntil: "networkidle" })
  await page.getByLabel("Your password").fill("wrong-password")
  await page.getByRole("checkbox").check()
  await page.getByRole("button", { name: "Delete my account" }).click()
  const wrong = await page.getByRole("alert").first().textContent({ timeout: 8000 }).catch(() => "")
  check("wrong password is refused with a visible error", /incorrect/i.test(wrong), wrong)
  await page.getByLabel("Your password").fill(process.env.DELETE_PASSWORD)
  await page.getByRole("button", { name: "Delete my account" }).click()
  const done = await page.locator('[role="status"]', { hasText: "has been deleted" }).first().textContent({ timeout: 10000 }).catch(() => "")
  check("deletion succeeds and says what was kept", /has been deleted/i.test(done) && /kept/i.test(done), done.slice(0, 90))
  const signedOut = await page.waitForFunction(() => !localStorage.getItem("access") && !localStorage.getItem("refresh"), null, { timeout: 5000 }).then(() => true).catch(() => false)
  check("signed out afterwards", signedOut, await page.evaluate(() => Object.keys(localStorage).join(",")))
  await ctx.close()
}

await browser.close()
const failed = results.filter((r) => !r.ok)
console.log(`\n${results.length - failed.length}/${results.length} passed`)
process.exit(failed.length ? 1 : 0)
