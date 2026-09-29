// Rendered-site audit: titles, descriptions, canonical, headings, horizontal
// overflow (with the offending elements), unnamed controls, images without
// alt, empty links and console errors, per route and viewport.
//
//   BASE_URL=http://localhost:5173 node scripts/site-audit.mjs [route ...]
//
// Writes site-audit.json (git-ignored) and prints a summary. Uses the same
// browser selection as the e2e suite (e2e/chromium.js).
import { writeFileSync } from "node:fs"
import { chromium } from "@playwright/test"
import { browserLaunchOptions } from "../e2e/chromium.js"

const BASE = process.env.BASE_URL || "http://localhost:5173"
const WIDTHS = (process.env.WIDTHS || "320,375,390,414,768,1280,1440,1920").split(",").map(Number)
const ROUTES = process.argv.slice(2).length ? process.argv.slice(2) : [
  "/", "/destinations", "/destinations/namche-bazaar-sherpa-capital", "/districts", "/districts/Kaski",
  "/compare", "/decide", "/discover", "/search?q=pokhara", "/gallery", "/itinerary", "/packages",
  "/recommendation", "/guides", "/emergency", "/before-you-travel", "/budget-estimator", "/risk-alerts",
  "/navigation", "/distances", "/nearby-places", "/hotels/search", "/language", "/translation",
  "/discover-nepal", "/explore-map", "/about", "/contact", "/support", "/how-it-works", "/knowledge-base",
  "/privacy", "/terms", "/privacy-policy", "/terms-of-service", "/cookie-policy", "/data-deletion", "/unsubscribe",
  "/login", "/register", "/forgot-password", "/this-page-does-not-exist",
]

const collect = () => {
  const vw = document.documentElement.clientWidth
  const overflow = []
  if (document.documentElement.scrollWidth > vw + 1) {
    for (const el of document.querySelectorAll("body *")) {
      const r = el.getBoundingClientRect()
      if (r.width === 0 || r.height === 0) continue
      if (r.right > vw + 1 || r.left < -1) {
        // Skip descendants of elements that clip their own overflow.
        let p = el.parentElement, clipped = false
        while (p && p !== document.body) {
          const s = getComputedStyle(p)
          if (/(hidden|auto|scroll|clip)/.test(s.overflowX)) { clipped = true; break }
          p = p.parentElement
        }
        if (clipped) continue
        const s = getComputedStyle(el)
        if (s.position === "fixed" && s.visibility === "hidden") continue
        overflow.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}.${String(el.className?.baseVal ?? el.className).split(" ").slice(0, 4).join(".")} [${Math.round(r.left)}..${Math.round(r.right)}]`)
      }
    }
  }
  const name = (el) => (el.getAttribute("aria-label") || el.getAttribute("title") || el.textContent || "").trim()
    || [...el.querySelectorAll("img[alt]")].map((i) => i.alt).join("").trim()
    || (el.getAttribute("aria-labelledby") && document.getElementById(el.getAttribute("aria-labelledby"))?.textContent?.trim())
  const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 }
  return {
    title: document.title,
    description: document.querySelector('meta[name="description"]')?.content || "",
    canonical: document.querySelector('link[rel="canonical"]')?.href || "",
    h1: [...document.querySelectorAll("h1")].filter(visible).map((h) => h.textContent.trim().slice(0, 80)),
    scrollWidth: document.documentElement.scrollWidth, clientWidth: vw,
    overflow: overflow.slice(0, 8),
    imgNoAlt: [...document.querySelectorAll("img")].filter((i) => !i.hasAttribute("alt") && visible(i)).map((i) => i.src.slice(0, 100)).slice(0, 8),
    badAlt: [...document.querySelectorAll("img[alt]")].filter((i) => /^(image|photo|picture|img[_-]?\d*|untitled)$/i.test(i.alt.trim())).map((i) => i.alt).slice(0, 5),
    unnamedButtons: [...document.querySelectorAll("button, [role=button]")].filter((b) => visible(b) && !name(b)).map((b) => b.outerHTML.slice(0, 120)).slice(0, 6),
    unnamedLinks: [...document.querySelectorAll("a[href]")].filter((a) => visible(a) && !name(a)).map((a) => a.outerHTML.slice(0, 120)).slice(0, 6),
    // A few map libraries implement zoom controls as labelled anchors. Once
    // they carry role=button they are controls, not navigation links; audit
    // them through unnamedButtons instead of flagging their placeholder URL.
    emptyLinks: [...document.querySelectorAll("a")].filter((a) => visible(a) && a.getAttribute("role") !== "button" && (!a.getAttribute("href") || a.getAttribute("href") === "#")).map((a) => a.outerHTML.slice(0, 120)).slice(0, 6),
    unlabelledInputs: [...document.querySelectorAll("input:not([type=hidden]), select, textarea")].filter((i) => visible(i)
      && !i.getAttribute("aria-label") && !i.getAttribute("aria-labelledby") && !(i.id && document.querySelector(`label[for="${CSS.escape(i.id)}"]`)) && !i.closest("label")).map((i) => i.outerHTML.slice(0, 120)).slice(0, 6),
    internalLinks: [...new Set([...document.querySelectorAll("a[href^='/']")].map((a) => a.getAttribute("href").split("#")[0]))],
  }
}

const launchOptions = await browserLaunchOptions()
const browser = await chromium.launch(launchOptions)
const out = {}
for (const route of ROUTES) {
  out[route] = {}
  for (const width of WIDTHS) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, serviceWorkers: "block" })
    const page = await context.newPage()
    const errors = []
    page.on("pageerror", (e) => errors.push(String(e.message).slice(0, 160)))
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 160)) })
    try {
      await page.goto(BASE + route, { waitUntil: "networkidle", timeout: 30000 })
    } catch { /* keep whatever rendered */ }
    await page.waitForTimeout(400)
    // UNCLIP_SHELL=1: turn off the app shell's overflow-x clipping first, so
    // content that only "fits" because the shell clips it is reported.
    if (process.env.UNCLIP_SHELL) {
      await page.evaluate(() => document.querySelectorAll(".ny-app-shell").forEach((el) => { el.style.overflowX = "visible" })).catch(() => {})
      await page.waitForTimeout(150)
    }
    const data = await page.evaluate(collect).catch((e) => ({ error: String(e) }))
    data.errors = [...new Set(errors)].slice(0, 5)
    out[route][width] = data
    await context.close()
  }
  const d = out[route][WIDTHS.at(-1)] || {}
  const over = WIDTHS.filter((w) => out[route][w].overflow?.length).join(",")
  console.log(`${route}\n  title: ${d.title}\n  desc: ${(d.description || "").slice(0, 90)}\n  h1: ${JSON.stringify(d.h1)}  overflow@: ${over || "none"}  noAlt:${d.imgNoAlt?.length} unnamedBtn:${d.unnamedButtons?.length} unnamedLink:${d.unnamedLinks?.length} unlabelled:${d.unlabelledInputs?.length} errors:${d.errors?.length}`)
}
await browser.close()
writeFileSync("site-audit.json", JSON.stringify(out, null, 2))
