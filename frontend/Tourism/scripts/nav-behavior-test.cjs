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
global.SVGElement = window.SVGElement
global.AbortController = window.AbortController
global.AbortSignal = window.AbortSignal
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

  // =========================================================================
  // COOKIE CONSENT BANNER (§17) — real component, fixture-driven public config
  // =========================================================================
  const consentSel = '[aria-label="Cookie consent"]'
  const consentStorage = window.localStorage

  // --- no setting saved yet: banner shows with privacy link ------------------
  consentStorage.removeItem("tourism_cookie_consent")
  entry.setPublicConfigFixture({ settings: {}, pages: [], navigation: [] })
  const c1 = entry.mountCookieBanner()
  await settle()
  check("cookie: shown by default when no setting saved", !!$(c1.container, consentSel))
  check("cookie: links the privacy policy", !!$(c1.container, 'a[href="/privacy"]'))
  c1.unmount()

  // --- CMS disables it: hidden ------------------------------------------------
  entry.setPublicConfigFixture({ settings: { cookie_consent: { enabled: false, message: "x" } }, pages: [], navigation: [] })
  const c2 = entry.mountCookieBanner()
  await settle()
  check("cookie: hidden when the CMS setting disables it", !$(c2.container, consentSel))
  c2.unmount()

  // --- custom CMS message reaches the visitor --------------------------------
  entry.setPublicConfigFixture({ settings: { cookie_consent: { enabled: true, message: "Custom wording here" } }, pages: [], navigation: [] })
  const c3 = entry.mountCookieBanner()
  await settle()
  check("cookie: custom CMS message rendered", /Custom wording here/.test(c3.container.textContent))
  c3.unmount()

  // --- Accept hides it and persists the choice --------------------------------
  entry.setPublicConfigFixture({ settings: { cookie_consent: { enabled: true } }, pages: [], navigation: [] })
  const c4 = entry.mountCookieBanner()
  await settle()
  const acceptBtn = [...c4.container.querySelectorAll("button")].find((b) => /Accept/.test(b.textContent))
  check("cookie: Accept button present", !!acceptBtn)
  await click(acceptBtn)
  check("cookie: Accept hides the banner", !$(c4.container, consentSel))
  check("cookie: Accept persisted to localStorage", consentStorage.getItem("tourism_cookie_consent") === "accepted")
  c4.unmount()

  // --- a visitor who already accepted never sees it again ---------------------
  const c5 = entry.mountCookieBanner()
  await settle()
  check("cookie: stays hidden after a prior Accept", !$(c5.container, consentSel))
  c5.unmount()
  consentStorage.removeItem("tourism_cookie_consent")

  // =========================================================================
  // NEARBY PLACES PAGE (real component, stubbed transport + geolocation).
  // Traces API data -> component state -> rendered cards, and pins that no
  // failure mode ever renders the old generic "No nearby places found".
  // =========================================================================
  const nearbyRow = (id, name, slug, lat, lng, km) => ({
    id, name, slug, latitude: lat, longitude: lng, distance_km: km,
    city: "Kathmandu", district: "Kathmandu", province: "Bagmati Province",
    category_name: "Heritage", average_rating: 4.5, ratings_count: 10,
    views_count: 100, cover_image_url: null, status: "APPROVED",
    is_user_submitted: false, is_active: true,
  })

  // --- A. GPS fix renders real cards with distance + detail links ------------
  entry.setGeolocation("success", { lat: 27.7172, lng: 85.324 })
  entry.setNearbyFixture({
    results: [
      nearbyRow(11, "Patan Durbar Square", "patan-durbar-square", 27.671, 85.316, 5.2),
      nearbyRow(12, "Swayambhunath Stupa", "swayambhunath-stupa", 27.7149, 85.2904, 3.4),
    ],
  })
  const n1 = entry.mountNearbyPage()
  await settle()
  await settle()
  const txt1 = n1.container.textContent
  check("nearby: renders destination cards from the API result set",
    /Patan Durbar Square/.test(txt1) && /Swayambhunath Stupa/.test(txt1))
  check("nearby: shows server-computed distance", /5\.2 km/.test(txt1) && /3\.4 km/.test(txt1))
  check("nearby: cards link to existing detail routes",
    !!n1.container.querySelector('a[href="/destinations/patan-durbar-square"]'))
  check("nearby: directions links use recorded coordinates",
    n1.container.querySelectorAll('a[href*="google.com/maps/dir/?api=1&destination="]').length >= 2)
  check("nearby: summary reports count and radius", /Found 2 destinations within 25 km/.test(txt1))
  check("nearby: never shows the generic no-places copy", !/No nearby places found/i.test(txt1))
  const calls1 = entry.getNearbyCalls()
  check("nearby: sends backend param names latitude/longitude/radius_km",
    calls1.length >= 1 &&
    calls1[0].params.latitude === 27.7172 &&
    calls1[0].params.longitude === 85.324 &&
    calls1[0].params.radius_km === 25)
  check("nearby: map markers come from the same result set",
    n1.container.querySelectorAll(".leaflet-marker-icon").length >= 2)
  n1.unmount()

  // --- B. permission denial is its own state, not "empty" ---------------------
  entry.setGeolocation("denied")
  entry.setNearbyFixture({ results: [] })
  const n2 = entry.mountNearbyPage()
  await settle()
  await settle()
  const txt2 = n2.container.textContent
  check("nearby: denial says location is off, never 'no nearby places'",
    /Location access is turned off/.test(txt2) && !/No nearby places found/i.test(txt2))
  check("nearby: denial offers Try Again and Choose Location",
    /Try Again/.test(txt2) && /Choose Location/.test(txt2))
  check("nearby: denial fires no nearby query", entry.getNearbyCalls().length === 0)
  n2.unmount()

  // --- C. API failure has a Retry that recovers --------------------------------
  entry.setGeolocation("success", { lat: 27.7172, lng: 85.324 })
  entry.setNearbyFixture({
    failOnce: true,
    results: [nearbyRow(11, "Patan Durbar Square", "patan-durbar-square", 27.671, 85.316, 5.2)],
  })
  const n3 = entry.mountNearbyPage()
  await settle()
  await settle()
  check("nearby: API failure gets its own message",
    /couldn't be loaded/.test(n3.container.textContent))
  const retryBtn = [...n3.container.querySelectorAll("button")].find((b) => /Retry/.test(b.textContent))
  check("nearby: API failure offers Retry", !!retryBtn)
  await click(retryBtn)
  await settle()
  await settle()
  check("nearby: Retry recovers and renders cards",
    /Patan Durbar Square/.test(n3.container.textContent))
  n3.unmount()

  // --- D. genuine empty offers radius expansion, which refetches ---------------
  entry.setGeolocation("success", { lat: 27.7172, lng: 85.324 })
  entry.setNearbyFixture({ results: [], count: 0 })
  const n4 = entry.mountNearbyPage()
  await settle()
  await settle()
  const txt4 = n4.container.textContent
  check("nearby: true empty states the radius, not a generic message",
    /No destinations found within 25 km/.test(txt4) && !/No nearby places found/i.test(txt4))
  const expandBtn = [...n4.container.querySelectorAll("button")].find((b) => /Expand to 50 km/.test(b.textContent))
  check("nearby: empty offers radius expansion", !!expandBtn)
  await click(expandBtn)
  await settle()
  await settle()
  const calls4 = entry.getNearbyCalls()
  check("nearby: expansion refetches with radius_km=50",
    calls4.length >= 2 && calls4[calls4.length - 1].params.radius_km === 50)
  n4.unmount()

  // --- E. manual origin picker drives the query and excludes the origin --------
  entry.setGeolocation("denied")
  entry.setNearbyFixture({
    results: [
      nearbyRow(999, "Phewa Lakeside Test", "phewa-lakeside", 28.2096, 83.9856, 0.0),
      nearbyRow(1000, "World Peace Stupa Test", "world-peace-stupa", 28.191, 83.94, 4.9),
    ],
  })
  entry.setSearchFixture([nearbyRow(999, "Phewa Lakeside Test", "phewa-lakeside", 28.2096, 83.9856, 0)])
  const n5 = entry.mountNearbyPage()
  await settle()
  await settle()
  const chooseBtn = [...n5.container.querySelectorAll("button")].find((b) => /Choose Location/.test(b.textContent))
  check("nearby: Choose Location opens the picker", !!chooseBtn)
  await click(chooseBtn)
  const pickerInput = n5.container.querySelector('input[aria-label="Search destinations to use as a starting point"]')
  check("nearby: picker offers destination search", !!pickerInput)
  const valueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set
  await act(async () => {
    valueSetter.call(pickerInput, "phewa")
    pickerInput.dispatchEvent(new window.Event("input", { bubbles: true }))
    await new Promise((r) => setTimeout(r, 450)) // debounce is 350ms
  })
  const optBtn = [...n5.container.querySelectorAll("button")].find((b) => /Phewa Lakeside Test/.test(b.textContent))
  check("nearby: picker lists real destinations from the API", !!optBtn)
  await click(optBtn)
  await settle()
  await settle()
  const calls5 = entry.getNearbyCalls()
  const last5 = calls5[calls5.length - 1]
  check("nearby: chosen origin coordinates drive the query",
    !!last5 && last5.params.latitude === 28.2096 && last5.params.longitude === 83.9856)
  check("nearby: origin destination excluded from its own results",
    !n5.container.querySelector('a[href="/destinations/phewa-lakeside"]') &&
    !!n5.container.querySelector('a[href="/destinations/world-peace-stupa"]'))
  n5.unmount()

  // --- F. Hotels tab renders real hotel cards from /hotels/nearby/ -------------
  const hotelRow = (id, name, lat, lng, km) => ({
    id, name, address: "Lakeside Road", latitude: lat, longitude: lng,
    price_per_night: "4500.00", currency: "NPR", rating: "4.50",
    booking_status: "available", booking_url: "", image_url: null,
    destination: 1, destination_name: "Lakeside Hub", destination_slug: "lakeside-hub",
    distance_km: km,
  })
  const tabButton = (container, label) =>
    [...container.querySelectorAll('button[role="tab"]')].find((b) => b.textContent.trim() === label)

  entry.setGeolocation("success", { lat: 28.2096, lng: 83.9856 })
  entry.setNearbyFixture({ results: [], count: 0 })
  entry.setHotelFixture({
    results: [
      hotelRow(501, "Lakeside Inn", 28.205, 83.98, 0.8),
      hotelRow(502, "Mountain View Resort", 28.3, 84.1, 15.2),
    ],
  })
  const n6 = entry.mountNearbyPage()
  await settle()
  await settle()
  const hotelsTab = tabButton(n6.container, "Hotels")
  check("nearby: Hotels tab is available", !!hotelsTab)
  await click(hotelsTab)
  await settle()
  await settle()
  const txt6 = n6.container.textContent
  check("nearby: hotels tab renders hotel cards from the API",
    /Lakeside Inn/.test(txt6) && /Mountain View Resort/.test(txt6))
  check("nearby: hotels show distance from the origin", /0\.8 km from/.test(txt6))
  check("nearby: hotels summary counts the type", /Found 2 hotels within 25 km/.test(txt6))
  const calls6 = entry.getHotelCalls()
  check("nearby: hotels query uses latitude/longitude/radius_km",
    calls6.length >= 1 &&
    calls6[0].params.latitude === 28.2096 &&
    calls6[0].params.longitude === 83.9856 &&
    calls6[0].params.radius_km === 25)
  n6.unmount()

  // --- G. Hospitals tab renders distance-ranked hospital rows ------------------
  entry.setGeolocation("success", { lat: 27.7172, lng: 85.324 })
  entry.setEmergencyFixture({
    hospitals: [{
      id: 71, type: "hospital", name: "Ciwec Hospital", address: "Hattisar",
      district: "Kathmandu", phone_number: "01-4424111",
      latitude: 27.7131, longitude: 85.3218, distance_km: 0.5,
    }],
  })
  const n7 = entry.mountNearbyPage()
  await settle()
  await settle()
  const hospTab = tabButton(n7.container, "Hospitals")
  check("nearby: Hospitals tab is available", !!hospTab)
  await click(hospTab)
  await settle()
  await settle()
  const txt7 = n7.container.textContent
  check("nearby: hospitals tab renders real hospital rows",
    /Ciwec Hospital/.test(txt7) && /0\.5 km away/.test(txt7))
  check("nearby: hospital rows expose a callable phone link",
    !!n7.container.querySelector('a[href="tel:01-4424111"]'))
  check("nearby: hospital rows offer directions from recorded coordinates",
    n7.container.querySelectorAll('a[href*="destination=27.7131,85.3218"]').length >= 1)
  const calls7 = entry.getEmergencyCalls()
  check("nearby: hospitals query sends latitude/longitude/radius_km",
    calls7.length >= 1 &&
    calls7[0].params.latitude === 27.7172 &&
    calls7[0].params.longitude === 85.324 &&
    calls7[0].params.radius_km === 25)
  n7.unmount()

  // --- H. empty wording is per-type ---------------------------------------------
  entry.setGeolocation("success", { lat: 27.7172, lng: 85.324 })
  entry.setNearbyFixture({ results: [], count: 0 })
  entry.setHotelFixture({ results: [], count: 0 })
  const n8 = entry.mountNearbyPage()
  await settle()
  await settle()
  await click(tabButton(n8.container, "Hotels"))
  await settle()
  await settle()
  check("nearby: hotel empty state names the type and radius",
    /No hotels found within 25 km/.test(n8.container.textContent) &&
    !/No nearby places found/i.test(n8.container.textContent))
  n8.unmount()

  console.log(results.join("\n"))
  console.log(`\n${results.length - failures}/${results.length} passed`)
  process.exit(failures ? 1 : 0)
}

main().catch((e) => { console.error(e); process.exit(2) })
