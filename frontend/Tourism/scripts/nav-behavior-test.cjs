/* Functional hamburger/sidebar test — runs the REAL bundled components
   (Navbar, Sidebar, useSidebarState store, AdminLayout) inside jsdom with a
   width-aware matchMedia stub, exactly like a browser viewport.
   Usage: node scripts/nav-behavior-test.cjs                          */
const { JSDOM } = require("jsdom")
const path = require("path")

let failures = 0
const results = []
function check(name, cond, detail) {
  results.push(`${cond ? "PASS" : "FAIL"}  ${name}${detail && !cond ? `  -> ${detail}` : ""}`)
  if (!cond) failures++
}

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/",
  pretendToBeVisual: true,
})
const { window } = dom

// --- width-aware matchMedia stub (single source of truth: fakeWidth) -------
let fakeWidth = 1280
const mqls = new Set()
window.matchMedia = (query) => {
  const parse = (q) => {
    const min = q.match(/min-width:\s*(\d+)px/)
    const max = q.match(/max-width:\s*(\d+)px/)
    return { min: min ? +min[1] : null, max: max ? +max[1] : null }
  }
  const evaluate = () => {
    const { min, max } = parse(query)
    return (min === null || fakeWidth >= min) && (max === null || fakeWidth <= max)
  }
  const mql = {
    get matches() { return evaluate() },
    media: query,
    _handlers: new Set(),
    addEventListener: (_t, fn) => mql._handlers.add(fn),
    removeEventListener: (_t, fn) => mql._handlers.delete(fn),
    addListener: (fn) => mql._handlers.add(fn),
    removeListener: (fn) => mql._handlers.delete(fn),
    dispatchEvent: () => true,
  }
  mqls.add(mql)
  return mql
}

global.window = window
global.document = window.document
global.navigator = window.navigator
global.HTMLElement = window.HTMLElement
global.Element = window.Element
global.Node = window.Node
global.Event = window.Event
global.MouseEvent = window.MouseEvent
global.KeyboardEvent = window.KeyboardEvent
global.getComputedStyle = window.getComputedStyle
global.requestAnimationFrame = window.requestAnimationFrame
global.cancelAnimationFrame = window.cancelAnimationFrame
global.localStorage = window.localStorage
global.IS_REACT_ACT_ENVIRONMENT = true
window.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
global.ResizeObserver = window.ResizeObserver
window.scrollTo = () => {}

const entry = require(path.resolve(__dirname, "../tests-nav/nav-test-bundle.cjs"))
const { act } = entry

// Viewport change + full flush of React work and deferred timers, the way a
// browser would process a resize event.
async function setWidth(px) {
  fakeWidth = px
  await act(async () => {
    for (const mql of mqls) {
      const ev = { matches: mql.matches, media: mql.media }
      for (const fn of [...mql._handlers]) fn(ev)
    }
    await new Promise((r) => setTimeout(r, 10))
  })
}
async function settle() {
  await act(async () => { await new Promise((r) => setTimeout(r, 10)) })
}

const $ = (root, sel) => root.querySelector(sel)
const click = async (el) => {
  await act(async () => {
    el.dispatchEvent(new window.MouseEvent("click", { bubbles: true }))
    await new Promise((r) => setTimeout(r, 10))
  })
}

async function main() {
  // =========================================================================
  // TRAVELLER SHELL (Navbar + Sidebar + real store)
  // =========================================================================
  const t = entry.mountTravellerShell()
  await settle()
  const aside = () => $(t.container, "#sidebar-drawer")
  const hamburger = () => $(t.container, 'button[aria-controls="sidebar-drawer"]')
  const backdrop = () => $(t.container, '[data-sidebar-backdrop]')

  // --- DESKTOP 1280px: rail starts expanded, hamburger collapses to icons ---
  await setWidth(1280)
  check("desktop: hamburger exists at 1280px", !!hamburger())
  check("desktop: rail starts expanded (lg:w-64)", /lg:w-64/.test(aside().className), aside().className)
  await click(hamburger())
  check("desktop: click -> icon rail (lg:w-16)", /lg:w-16/.test(aside().className), aside().className)
  check("desktop: rail still on-screen (lg:translate-x-0)", /lg:translate-x-0/.test(aside().className))
  check("desktop: hamburger aria-expanded=false", hamburger().getAttribute("aria-expanded") === "false")
  check("desktop: no scroll-lock while collapsed", !window.document.body.classList.contains("sidebar-open"))
  check("desktop: collapsed shows icon links w/ hidden labels", (() => {
    const spans = [...aside().querySelectorAll("a span")]
    return spans.length > 0 && spans.every((s) => /lg:hidden/.test(s.className) || s.textContent.trim() === "")
  })(), `${aside().querySelectorAll("a span").length} spans`)
  await click(hamburger())
  check("desktop: click again -> expanded (lg:w-64)", /lg:w-64/.test(aside().className), aside().className)

  // --- TABLET 768px: hamburger opens overlay drawer -------------------------
  await setWidth(768)
  check("tablet: drawer closed after crossing to <lg", /-translate-x-full/.test(aside().className), aside().className)
  await click(hamburger())
  check("tablet: click -> drawer opens (translate-x-0)", /(^| )translate-x-0/.test(aside().className), aside().className)
  check("tablet: body scroll-lock applied", window.document.body.classList.contains("sidebar-open"))
  await click(backdrop())
  check("tablet: backdrop click closes drawer", /-translate-x-full/.test(aside().className))
  check("tablet: scroll-lock released", !window.document.body.classList.contains("sidebar-open"))

  // --- MOBILE 375px: same drawer behavior ----------------------------------
  await setWidth(375)
  await click(hamburger())
  check("mobile: click -> drawer opens", /(^| )translate-x-0/.test(aside().className))
  check("mobile: expanded menu shows text labels (not lg:hidden)", (() => {
    const spans = [...aside().querySelectorAll("a span")].filter((s) => s.textContent.trim())
    return spans.length > 0 && spans.some((s) => !/lg:hidden/.test(s.className))
  })(), `${aside().querySelectorAll("a span").length} spans`)
  await act(async () => {
    window.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }))
    await new Promise((r) => setTimeout(r, 10))
  })
  check("mobile: Escape closes drawer", /-translate-x-full/.test(aside().className))

  // --- mandatory resize scenario (§43) -------------------------------------
  await click(hamburger()) // open drawer on mobile
  await setWidth(1280)
  check("resize mobile(open)->desktop: no stale drawer (rail visible, no scroll-lock)",
    /lg:translate-x-0/.test(aside().className) && !window.document.body.classList.contains("sidebar-open"))
  await setWidth(375)
  check("resize desktop->mobile: drawer closed, content not covered", /-translate-x-full/.test(aside().className), aside().className)

  t.unmount()

  // =========================================================================
  // ADMIN SHELL (AdminLayout)
  // =========================================================================
  const a = entry.mountAdminShell()
  await settle()
  const aAside = () => $(a.container, "#admin-navigation")
  const aHamburger = () => $(a.container, 'button[aria-controls="admin-navigation"]')
  const aMain = () => $(a.container, "#admin-main")
  const aBackdrop = () => [...a.container.querySelectorAll("button")].find((b) => /Close admin navigation overlay/.test(b.getAttribute("aria-label") || ""))

  await setWidth(1440)
  check("admin desktop: hamburger exists", !!aHamburger())
  check("admin desktop: rail starts expanded (lg:w-72)", /lg:w-72/.test(aAside().className), aAside().className)
  check("admin desktop: active-section group auto-opened (Reports reachable)",
    [...aAside().querySelectorAll("a")].some((x) => /section=reports/.test(x.getAttribute("href") || "")),
    `${aAside().querySelectorAll("a").length} links total`)
  await click(aHamburger())
  check("admin desktop: click -> icon rail (lg:w-16)", /lg:w-16/.test(aAside().className), aAside().className)
  check("admin desktop: content expands (lg:pl-16)", /lg:pl-16/.test(aMain().className), aMain().className)
  check("admin desktop: link labels hidden in rail (no vertical text)", (() => {
    const spans = [...aAside().querySelectorAll("a span")].filter((s) => s.textContent.trim())
    return spans.length > 0 && spans.every((s) => /lg:hidden/.test(s.className))
  })(), `${[...aAside().querySelectorAll("a span")].filter((s) => s.textContent.trim()).length} visible-label spans`)
  check("admin desktop: all sections still reachable collapsed", aAside().querySelectorAll("nav a").length >= 10,
    `${aAside().querySelectorAll("nav a").length} links`)
  await click(aHamburger())
  check("admin desktop: click again -> expanded (lg:w-72) + content lg:pl-72",
    /lg:w-72/.test(aAside().className) && /lg:pl-72/.test(aMain().className))

  await setWidth(820) // tablet
  check("admin tablet: drawer closed after crossing", /-translate-x-full/.test(aAside().className), aAside().className)
  await click(aHamburger())
  check("admin tablet: click -> drawer opens", /(^| )translate-x-0/.test(aAside().className), aAside().className)
  await click(aBackdrop())
  check("admin tablet: overlay click closes", /-translate-x-full/.test(aAside().className))

  await setWidth(390) // mobile
  await click(aHamburger())
  check("admin mobile: click -> drawer opens", /(^| )translate-x-0/.test(aAside().className))
  await setWidth(1440)
  check("admin resize mobile(open)->desktop: stale drawer cleared",
    /-translate-x-full/.test(aAside().className) && /lg:translate-x-0/.test(aAside().className), aAside().className)

  a.unmount()

  console.log(results.join("\n"))
  console.log(`\n${results.length - failures}/${results.length} passed`)
  process.exit(failures ? 1 : 0)
}

main().catch((e) => { console.error(e); process.exit(2) })
