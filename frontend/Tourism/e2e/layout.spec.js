import { test, expect } from "@playwright/test"

// Layout & overlap guard.
// For every key route at a spread of viewport widths, assert:
//   1. No unintended horizontal scrolling (content fits the viewport).
//   2. No two visible, non-nested text/badge elements overlap significantly.
// This is the "does it actually view perfectly on mobile & desktop" check.

const ROUTES = [
  "/",
  "/destinations",
  "/hotels",
  "/emergency",
  "/budget-estimator",
  "/recommendation",
  "/itinerary",
  "/packages",
  "/gallery",
  "/discover-nepal",
  "/compare",
  "/translation",
  "/language",
  "/navigation",
  "/family-safety",
  "/risk-alerts",
  "/chatbot",
  "/trip",
]

const WIDTHS = [320, 375, 414, 768, 1024, 1280]

// Returns the count of significantly-overlapping visible element pairs.
async function countOverlaps(page) {
  return page.evaluate(() => {
    const isTextual = (el) => {
      const tag = el.tagName
      return (
        ["H1", "H2", "H3", "H4", "H5", "H6", "P", "SPAN", "B", "STRONG", "BUTTON", "A", "LABEL"].includes(tag) &&
        (el.innerText || "").trim().length > 0
      )
    }
    const visible = (el) => {
      const r = el.getBoundingClientRect()
      const st = getComputedStyle(el)
      return r.width > 1 && r.height > 1 && st.visibility !== "hidden" && st.display !== "none"
    }
    // Only sample leaf-ish textual elements to keep the pair count tractable.
    const els = Array.from(document.querySelectorAll("h1,h2,h3,h4,p,span,button,a,label"))
      .filter(isTextual)
      .filter(visible)
      .filter((el) => !el.querySelector("h1,h2,h3,h4,p,button")) // skip wrappers
    const rects = els.map((el) => el.getBoundingClientRect())
    let overlaps = 0
    const samples = []
    const inter = (a, b) => {
      const x = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left))
      const y = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top))
      return x * y
    }
    const area = (r) => r.width * r.height
    const desc = (el) => {
      const cls = (el.className && String(el.className).split(/\s+/)[0]) || ""
      return `${el.tagName.toLowerCase()}${cls ? "." + cls : ""}["${(el.innerText || "").trim().slice(0, 24).replace(/\n/g, " ")}"]`
    }
    for (let i = 0; i < rects.length; i++) {
      for (let j = i + 1; j < rects.length; j++) {
        const a = rects[i], b = rects[j]
        const elA = els[i], elB = els[j]
        if (elA.contains(elB) || elB.contains(elA)) continue // nested is fine
        const o = inter(a, b)
        if (o <= 0) continue
        const smaller = Math.min(area(a), area(b))
        if (smaller > 0 && o / smaller > 0.5) {
          overlaps++
          if (samples.length < 8) samples.push(`${desc(elA)} X ${desc(elB)}`)
        }
      }
    }
    return { count: overlaps, samples }
  })
}

for (const route of ROUTES) {
  for (const width of WIDTHS) {
    test(`no horizontal overflow + no text overlap ${route} @${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 })
      await page.goto(route, { waitUntil: "domcontentloaded" })
      // Give lazy images / data a moment to settle.
      await page.waitForTimeout(1200)

      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth
      )
      expect(overflow, `horizontal overflow of ${overflow}px at ${width}px`).toBeLessThanOrEqual(1)

      const overlaps = await countOverlaps(page)
      expect(
        overlaps.count,
        `${overlaps.count} overlapping text pairs at ${width}px` +
          (overlaps.samples.length ? ` | ${overlaps.samples.join(" ; ")}` : "")
      ).toBe(0)
    })
  }
}
