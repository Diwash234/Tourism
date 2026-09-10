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
global.CustomEvent = window.CustomEvent
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

  // =========================================================================
  // ADMIN DATA EXPLORER — §21 province -> district -> municipality cascade
  // =========================================================================
  entry.setDataExplorerFixtures({
    list: {
      results: [{ id: 77, name: "Cascade Test Temple" }],
      count: 1, total_pages: 1, page: 1, columns: ["id", "name"],
    },
    detail: {
      id: 77, name: "Cascade Test Temple", city: "Kathmandu",
      province: "Bagmati", district: "Kathmandu",
      municipality: "Kathmandu Metropolitan City",
      ward_number: 3,
      latitude: "27.7172", longitude: "85.3240",
    },
  })
  const n9 = entry.mountDataExplorer()
  await settle()
  await settle()
  const row = [...n9.container.querySelectorAll("tr")].find((tr) => /Cascade Test Temple/.test(tr.textContent))
  check("geo: data explorer lists destination rows", !!row)
  await click(row)
  await settle()

  const fieldFor = (name) => {
    const label = [...n9.container.querySelectorAll("label")]
      .find((l) => l.textContent.trim().toLowerCase().startsWith(name))
    return label ? (label.querySelector("select") || label.querySelector("input")) : null
  }
  const optValues = (sel) => (sel && sel.tagName === "SELECT" ? [...sel.options].map((o) => o.value) : [])

  const provSel = fieldFor("province")
  const distSel = fieldFor("district")
  const muniSel = fieldFor("municipality")
  check("geo: province renders as a select of the 7 provinces",
    !!provSel && provSel.tagName === "SELECT" && provSel.options.length === 8 && provSel.value === "Bagmati")
  const distOpts = optValues(distSel)
  check("geo: district options are filtered to the selected province",
    distOpts.includes("Kathmandu") && distOpts.includes("Bhaktapur") && !distOpts.includes("Kaski"))
  check("geo: municipality options come from the district's recorded list",
    optValues(muniSel).includes("Kathmandu Metropolitan City") &&
    muniSel.value === "Kathmandu Metropolitan City")

  // Changing the province must drop child values that would be invalid.
  const selectSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set
  await act(async () => {
    selectSetter.call(provSel, "Gandaki")
    provSel.dispatchEvent(new window.Event("change", { bubbles: true }))
    await new Promise((r) => setTimeout(r, 10))
  })
  await settle()
  const distSel2 = fieldFor("district")
  const distOpts2 = optValues(distSel2)
  check("geo: changing province clears an invalid district and refilters options",
    distSel2.value === "" && distOpts2.includes("Kaski") && !distOpts2.includes("Kathmandu"))
  check("geo: municipality cleared along with the invalid district",
    fieldFor("municipality").value === "")
  const wardField = fieldFor("ward number")
  check("geo: ward number field offered (§21 ward tier)", !!wardField)
  check("geo: recorded ward loads into the form",
    !!wardField && wardField.value === "3", wardField && wardField.value)
  n9.unmount()

  // --- admin category CRUD rides the slug detail route (§22) ---------------
  // CategoryViewSet uses lookup_field="slug"; the panel must never send the
  // numeric id to PATCH/DELETE or every edit/delete silently 404s.
  window.confirm = () => true
  global.confirm = window.confirm
  entry.setCategoryFixture([
    { id: 7, slug: "lakes", name: "Lakes", icon: "water", description: "" },
    { id: 8, slug: "museums", name: "Museums", icon: "museum", description: "" },
  ])
  const n10 = entry.mountCategoryPanel()
  await settle()
  await settle()
  const catButtons = (label) =>
    [...n10.container.querySelectorAll("button")].filter((b) => b.textContent.trim() === label)
  check("categories: panel lists fixture rows", catButtons("Edit").length === 2,
    `edit buttons=${catButtons("Edit").length}`)
  await click(catButtons("Edit")[0])
  const catNameInput = n10.container.querySelector("input.input-field")
  check("categories: edit populates the form",
    !!catNameInput && catNameInput.value === "Lakes", catNameInput && catNameInput.value)
  check("categories: edit switches the button to Update", catButtons("Update").length === 1)
  await click(catButtons("Update")[0])
  const catPatch = entry.getCategoryCalls().find((c) => c.method === "patch")
  check("categories: PATCH targets the slug detail route",
    !!catPatch && catPatch.url.includes("/categories/lakes/"), catPatch && catPatch.url)
  check("categories: PATCH never targets the numeric id",
    !entry.getCategoryCalls().some((c) => /\/categories\/7\/?$/.test(c.url)))
  await click(catButtons("Delete")[0])
  const catDelete = entry.getCategoryCalls().find((c) => c.method === "delete")
  check("categories: DELETE targets the slug detail route",
    !!catDelete && catDelete.url.includes("/categories/lakes/"), catDelete && catDelete.url)
  n10.unmount()

  // --- database explorer: in-app CRUD, no raw Django admin (§33) ----------
  // The brief's most-important rule: routine add/edit/delete must never send
  // the administrator to the raw Django admin.
  window.confirm = () => true
  global.confirm = window.confirm
  entry.setDataExplorerFixtures({
    list: {
      results: [{ id: 77, name: "Cascade Test Temple" }],
      count: 1, total_pages: 1, page: 1, columns: ["id", "name"],
    },
    detail: {
      id: 77, name: "Cascade Test Temple", city: "Kathmandu",
      province: "Bagmati", district: "Kathmandu",
      municipality: "Kathmandu Metropolitan City",
      latitude: "27.7172", longitude: "85.3240",
    },
  })
  const n11 = entry.mountDataExplorer()
  await settle()
  await settle()
  check("explorer: no raw Django admin redirect link",
    !n11.container.querySelector('a[href="/django-admin/"]'))
  const addBtn = [...n11.container.querySelectorAll("button")].find((b) => /Add Destination/.test(b.textContent))
  check("explorer: in-app Add Destination button", !!addBtn)
  await click(addBtn)
  const createHeading = [...n11.container.querySelectorAll("h3")].find((h) => /Add Destination/.test(h.textContent))
  check("explorer: create form opens in-app", !!createHeading)
  const nameInput = n11.container.querySelector("input.input-field")
  check("explorer: create form has a name field", !!nameInput)
  await act(async () => {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set
    setter.call(nameInput, "Harness Created Place")
    nameInput.dispatchEvent(new window.Event("input", { bubbles: true }))
    await new Promise((r) => setTimeout(r, 10))
  })
  const createBtn = [...n11.container.querySelectorAll("button")].find((b) => /Create Destination/.test(b.textContent))
  check("explorer: create button offered", !!createBtn)
  await click(createBtn)
  const createCall = entry.getAdminDestinationCalls().find((c) => c.method === "post")
  check("explorer: create posts to the in-app API",
    !!createCall && /\/admin\/destinations\/?$/.test(createCall.url), createCall && createCall.url)
  check("explorer: create payload carries the name",
    !!createCall && String(createCall.data).includes("Harness Created Place"))
  const row11 = [...n11.container.querySelectorAll("tr")].find((tr) => /Cascade Test Temple/.test(tr.textContent))
  check("explorer: record row still listed", !!row11)
  await click(row11)
  await settle()
  const archiveBtn = [...n11.container.querySelectorAll("button")].find((b) => /Archive destination/.test(b.textContent))
  check("explorer: in-app archive offered", !!archiveBtn)
  await click(archiveBtn)
  const delCall = entry.getAdminDestinationCalls().find((c) => c.method === "delete")
  check("explorer: archive deletes via the in-app API",
    !!delCall && /\/admin\/destinations\/77$/.test(delCall.url), delCall && delCall.url)
  n11.unmount()

  // =========================================================================
  // AUTH RECOVERY (real axiosClient interceptors + real AuthContext)
  // =========================================================================
  const store = window.localStorage
  const sessionEvents = []
  const onExpiredEvt = () => sessionEvents.push("expired")
  const onDowngradedEvt = () => sessionEvents.push("downgraded")
  window.addEventListener("session-expired", onExpiredEvt)
  window.addEventListener("session-downgraded", onDowngradedEvt)
  const resetSession = ({ access, refresh, user }) => {
    store.clear()
    if (access) store.setItem("access", access)
    if (refresh) store.setItem("refresh", refresh)
    if (user) store.setItem("user", JSON.stringify(user))
    sessionEvents.length = 0
  }

  // --- A) stale access + stale refresh -> public data recovers anonymously --
  entry.setAuthFixture({ staleToken: "STALE", refreshStatus: 401 })
  resetSession({ access: "STALE", refresh: "DEAD_REFRESH", user: { username: "a" } })
  let resA = null
  let errA = null
  await entry.axiosClient.get("/destinations/").then((r) => { resA = r }).catch((e) => { errA = e })
  await settle()
  const callsA = entry.getAuthCalls()
  check("auth A: public list recovers after failed refresh", !!resA && resA.status === 200, errA && String(errA))
  check("auth A: exactly one refresh attempt", callsA.refresh === 1, `refresh=${callsA.refresh}`)
  check("auth A: retried once WITHOUT Authorization",
    JSON.stringify(callsA.destAuth) === JSON.stringify(["Bearer STALE", null]), JSON.stringify(callsA.destAuth))
  check("auth A: session storage cleared", !store.getItem("access") && !store.getItem("refresh") && !store.getItem("user"))
  check("auth A: downgraded event fired (user was signed in)", sessionEvents.includes("downgraded"), sessionEvents.join(","))
  check("auth A: no expired event for recoverable public read", !sessionEvents.includes("expired"), sessionEvents.join(","))

  // --- B) refresh success: one refresh for concurrent 401s, rotation kept ---
  entry.setAuthFixture({ staleToken: "STALE", refreshStatus: 200 })
  resetSession({ access: "STALE", refresh: "GOOD_REFRESH", user: { username: "a" } })
  const resB = await Promise.all([
    entry.axiosClient.get("/destinations/"),
    entry.axiosClient.get("/destinations/"),
    entry.axiosClient.get("/destinations/"),
  ])
  await settle()
  const callsB = entry.getAuthCalls()
  check("auth B: all three requests resolve", resB.every((r) => r.status === 200))
  check("auth B: single-flight -> exactly ONE refresh call", callsB.refresh === 1, `refresh=${callsB.refresh}`)
  check("auth B: rotated access token persisted", store.getItem("access") === "NEW_ACCESS", store.getItem("access"))
  check("auth B: rotated refresh token persisted (rotation+blacklist safe)",
    store.getItem("refresh") === "NEW_REFRESH", store.getItem("refresh"))
  check("auth B: queued retries carry the new token",
    callsB.destAuth.filter((a) => a === "Bearer NEW_ACCESS").length === 3, JSON.stringify(callsB.destAuth))
  check("auth B: no session events on healthy refresh", sessionEvents.length === 0, sessionEvents.join(","))

  // --- C) server rejects even the new token -> anonymous fallback, no loop --
  entry.setAuthFixture({ staleToken: "STALE", rejectNewToken: true, refreshStatus: 200 })
  resetSession({ access: "STALE", refresh: "GOOD_REFRESH", user: { username: "a" } })
  let resC = null
  await entry.axiosClient.get("/destinations/").then((r) => { resC = r }).catch(() => {})
  await settle()
  const callsC = entry.getAuthCalls()
  check("auth C: recovers anonymously when new token also rejected", !!resC && resC.status === 200)
  check("auth C: no refresh loop (one refresh, three attempts total)",
    callsC.refresh === 1 && callsC.destAuth.length === 3, `refresh=${callsC.refresh} attempts=${callsC.destAuth.length}`)
  check("auth C: attempt order stale -> new -> anonymous",
    JSON.stringify(callsC.destAuth) === JSON.stringify(["Bearer STALE", "Bearer NEW_ACCESS", null]), JSON.stringify(callsC.destAuth))

  // --- D) genuinely protected endpoint -> expired event + clean rejection --
  entry.setAuthFixture({ staleToken: "STALE", refreshStatus: 401 })
  resetSession({ access: "STALE", refresh: "DEAD_REFRESH", user: { username: "a" } })
  let errD = null
  await entry.axiosClient.get("/protected-probe/").then(() => {}, (e) => { errD = e })
  await settle()
  const callsD = entry.getAuthCalls()
  check("auth D: protected request rejects with 401", !!errD && errD.response && errD.response.status === 401)
  check("auth D: expired event fired for protected failure", sessionEvents.includes("expired"), sessionEvents.join(","))
  check("auth D: bounded retries (authed + one anonymous attempt)",
    callsD.destAuth.length === 2, JSON.stringify(callsD.destAuth))
  check("auth D: storage cleared for expired session", !store.getItem("access") && !store.getItem("user"))

  // --- E) anonymous 401: no storage churn, no events, no retry storm --------
  entry.setAuthFixture({ refreshStatus: 401 })
  resetSession({})
  let errE = null
  await entry.axiosClient.get("/protected-probe/").then(() => {}, (e) => { errE = e })
  await settle()
  check("auth E: anonymous protected 401 rejects", !!errE && errE.response.status === 401)
  check("auth E: no refresh attempted without a refresh token", entry.getAuthCalls().refresh === 0)
  check("auth E: no spurious session events for guests", sessionEvents.length === 0, sessionEvents.join(","))

  // --- F) AuthContext renders the session-expired banner --------------------
  resetSession({})
  entry.setAuthFixture({ refreshStatus: 401 })
  const auth = entry.mountAuthProvider()
  await settle()
  check("auth F: no banner initially", !auth.container.querySelector('[role="alert"]'))
  await act(async () => {
    window.dispatchEvent(new window.CustomEvent("session-expired"))
    await new Promise((r) => setTimeout(r, 10))
  })
  const banner = auth.container.querySelector('[role="alert"]')
  check("auth F: expired banner shown", !!banner && /session has expired/i.test(banner.textContent), banner && banner.textContent)
  check("auth F: banner offers sign-in", !!banner && !!banner.querySelector('a[href="/login"]'))
  const keepBrowsing = banner && [...banner.querySelectorAll("button")].find((b) => /Keep browsing/.test(b.textContent))
  check("auth F: dismiss button offered", !!keepBrowsing)
  if (keepBrowsing) await click(keepBrowsing)
  check("auth F: banner dismissible", !auth.container.querySelector('[role="alert"]'))
  auth.unmount()
  window.removeEventListener("session-expired", onExpiredEvt)
  window.removeEventListener("session-downgraded", onDowngradedEvt)
  store.clear()

  // --- off-route geometry: minDistanceToPathKm (increment 6) --------------
  const { minDistanceToPathKm } = entry
  const path2 = [
    { lat: 27.7172, lng: 85.3240 },
    { lat: 27.7272, lng: 85.3240 }, // ~1.11 km due north
  ]
  const onPath = minDistanceToPathKm(27.7222, 85.3240, path2)
  check("offroute: point on segment ~0", onPath !== null && onPath < 0.01, `got ${onPath}`)
  // ~0.01 deg lng at lat 27.7 ≈ 0.985 km east of the segment
  const east = minDistanceToPathKm(27.7222, 85.3340, path2)
  check("offroute: point 1 km east measured ~1 km", east !== null && east > 0.9 && east < 1.1, `got ${east}`)
  // Beyond segment end: clamps to the end vertex (~0.55 km past the north end)
  const past = minDistanceToPathKm(27.7322, 85.3240, path2)
  check("offroute: point past end clamps to vertex", past !== null && past > 0.5 && past < 0.62, `got ${past}`)
  check("offroute: null for empty path", minDistanceToPathKm(27.7, 85.3, []) === null)
  check("offroute: null for bad coords", minDistanceToPathKm(null, null, path2) === null)
  check("offroute: single-vertex path returns vertex distance", (() => {
    const d = minDistanceToPathKm(27.7272, 85.3240, [{ lat: 27.7172, lng: 85.3240 }])
    return d !== null && d > 1.0 && d < 1.2
  })())
  // Array-style [lat, lng] waypoints accepted too
  const arr = minDistanceToPathKm(27.7222, 85.3240, [[27.7172, 85.3240], [27.7272, 85.3240]])
  check("offroute: [lat,lng] arrays accepted", arr !== null && arr < 0.01, `got ${arr}`)

  // =========================================================================
  // LIVE NAVIGATION ENGINE (increment 7) — real LiveNavigationPanel +
  // real useLivePosition, synthetic routes/GPS only.
  // =========================================================================
  const liveRoute = [
    { lat: 28.2096, lng: 83.9856 }, // Pokhara
    { lat: 27.9634, lng: 84.6548 }, // midpoint
    { lat: 27.7172, lng: 85.3240 }, // Kathmandu
  ]
  const liveSteps = [
    { instruction: "Head north on NH2", distance_km: 65 },
    { instruction: "Continue to Kathmandu", distance_km: 65 },
  ]
  const basePanelProps = {
    route: liveRoute,
    steps: liveSteps,
    durationMin: 180,
    userPos: null,
    destinationName: "Kathmandu",
    onReroute: async () => false,
    onRecenter: () => {},
    onEnd: () => {},
  }

  // --- A: following state at the route start ------------------------------
  const panelA = entry.mountLiveNavPanel({ ...basePanelProps, userPos: { lat: 28.2096, lng: 83.9856 } })
  await settle()
  const textA = panelA.container.textContent
  check("live A: panel renders", !!panelA.container.querySelector('[data-testid="live-navigation-panel"]'))
  check("live A: following status at start", /Following route/.test(textA), textA.replace(/\s+/g, " ").slice(0, 100))
  const remA = Number((textA.match(/Remaining\s*([\d.]+)\s*km/) || [])[1])
  check("live A: remaining ≈ full route (~142 km)", remA > 135 && remA < 150, `got ${remA}`)
  const etaA = Number((textA.match(/ETA\s*(\d+)\s*min/) || [])[1])
  check("live A: ETA ≈ full duration at start", etaA > 160 && etaA <= 181, `got ${etaA}`)
  check("live A: next maneuver shown", /Head north on NH2/.test(textA))
  const offA = Number((textA.match(/GPS offset\s*(\d+)\s*m/) || [])[1])
  check("live A: GPS offset near zero on-route", offA < 20, `got ${offA}`)
  panelA.unmount()

  // --- B: arrival at the endpoint ------------------------------------------
  const panelB = entry.mountLiveNavPanel({ ...basePanelProps, userPos: { lat: 28.2096, lng: 83.9856 } })
  await settle()
  panelB.rerender({ ...basePanelProps, userPos: { lat: 27.7172, lng: 85.3240 } })
  await settle()
  const textB = panelB.container.textContent
  check("live B: arrival detected at endpoint", /Arrived at Kathmandu/.test(textB), textB.replace(/\s+/g, " ").slice(0, 100))
  check("live B: remaining zeroed on arrival", /Remaining\s*0 km/.test(textB))
  panelB.unmount()

  // --- C: off-route detection + successful reroute -------------------------
  const rerouteCalls = []
  const panelC = entry.mountLiveNavPanel({
    ...basePanelProps,
    userPos: { lat: 26.4567, lng: 87.2718 }, // Biratnagar — far off the route
    onReroute: async (lat, lng) => { rerouteCalls.push([lat, lng]); return true },
  })
  await settle()
  // Second fix (new object identity, same place) → consecutive off-route fixes.
  panelC.rerender({
    ...basePanelProps,
    userPos: { lat: 26.4567, lng: 87.2718 },
    onReroute: async (lat, lng) => { rerouteCalls.push([lat, lng]); return true },
  })
  await settle()
  await settle()
  check("live C: reroute requested from GPS position", rerouteCalls.length >= 1
    && rerouteCalls[0][0] === 26.4567 && rerouteCalls[0][1] === 87.2718, JSON.stringify(rerouteCalls))
  // Parent applies the rerouted path (as Navigation.jsx does) → back on route.
  const reroutedRoute = [
    { lat: 26.4567, lng: 87.2718 },
    { lat: 27.7172, lng: 85.3240 },
  ]
  panelC.rerender({
    ...basePanelProps,
    route: reroutedRoute,
    steps: [{ instruction: "Head to Kathmandu", distance_km: 150 }],
    userPos: { lat: 26.4567, lng: 87.2718 },
    onReroute: async (lat, lng) => { rerouteCalls.push([lat, lng]); return true },
  })
  await settle()
  const textC = panelC.container.textContent
  check("live C: following restored after reroute", /Following route/.test(textC), textC.replace(/\s+/g, " ").slice(0, 100))
  check("live C: reroute counter shown", /1 reroute/.test(textC), textC.replace(/\s+/g, " ").slice(0, 100))
  panelC.unmount()

  // --- D: failed reroute keeps honest off-route state -----------------------
  const panelD = entry.mountLiveNavPanel({
    ...basePanelProps,
    userPos: { lat: 26.4567, lng: 87.2718 },
    onReroute: async () => false,
  })
  await settle()
  panelD.rerender({ ...basePanelProps, userPos: { lat: 26.4567, lng: 87.2718 }, onReroute: async () => false })
  await settle()
  await settle()
  const textD = panelD.container.textContent
  check("live D: off-route state when reroute fails", /Off route/.test(textD) || /Rerouting/.test(textD), textD.replace(/\s+/g, " ").slice(0, 100))
  panelD.unmount()

  // --- E: recenter + end controls ------------------------------------------
  let recenters = 0
  let ended = 0
  const panelE = entry.mountLiveNavPanel({
    ...basePanelProps,
    userPos: { lat: 28.2096, lng: 83.9856 },
    onRecenter: () => { recenters += 1 },
    onEnd: () => { ended += 1 },
  })
  await settle()
  const recenterBtn = [...panelE.container.querySelectorAll("button")].find((b) => /Recenter on me/.test(b.textContent))
  const endBtn = [...panelE.container.querySelectorAll("button")].find((b) => /^End$/.test(b.textContent.trim()))
  check("live E: recenter button present", !!recenterBtn)
  check("live E: end button present", !!endBtn)
  if (recenterBtn) await click(recenterBtn)
  if (endBtn) await click(endBtn)
  check("live E: recenter callback fired", recenters === 1)
  check("live E: end callback fired", ended === 1)
  panelE.unmount()

  // --- E2: voice-guidance maneuver announcements -----------------------------
  const maneuvers = []
  const panelV = entry.mountLiveNavPanel({
    ...basePanelProps,
    userPos: { lat: 28.2096, lng: 83.9856 },
    onManeuver: (step) => maneuvers.push(step.instruction),
  })
  await settle()
  check("live E2: first maneuver announced", maneuvers.length === 1 && maneuvers[0] === "Head north on NH2", JSON.stringify(maneuvers))
  panelV.rerender({
    ...basePanelProps,
    userPos: { lat: 28.2097, lng: 83.9857 },
    onManeuver: (step) => maneuvers.push(step.instruction),
  })
  await settle()
  check("live E2: same maneuver not re-announced", maneuvers.length === 1, JSON.stringify(maneuvers))
  panelV.unmount()

  // --- F: useLivePosition (real hook, stubbed watchPosition) ----------------
  entry.setGeolocation("ok", { lat: 28.2, lng: 83.98 })
  const probe = entry.mountLiveProbe(true)
  await settle()
  check("live F: locating while awaiting first fix", probe.container.querySelector("#probe-locating").textContent === "true")
  check("live F: watch registered", entry.getWatchState().active === 1, JSON.stringify(entry.getWatchState()))
  entry.fireWatchFix({ lat: 28.21, lng: 83.99 })
  await settle()
  check("live F: fix surfaced to consumer", probe.container.querySelector("#probe-pos").textContent === "28.21,83.99")
  check("live F: locating clears after fix", probe.container.querySelector("#probe-locating").textContent === "false")
  probe.setActive(false)
  await settle()
  const ws = entry.getWatchState()
  check("live F: watch cleared on deactivate", ws.active === 0 && ws.clears === 1, JSON.stringify(ws))
  probe.unmount()

  // --- G: useLivePosition error honesty --------------------------------------
  entry.setGeolocation("denied")
  const probeG = entry.mountLiveProbe(true)
  entry.fireWatchError("User denied Geolocation", 1)
  await settle()
  check("live G: watch error surfaced", probeG.container.querySelector("#probe-err").textContent === "User denied Geolocation")
  probeG.unmount()
  entry.setGeolocation("unsupported")
  const probeH = entry.mountLiveProbe(true)
  await settle()
  check("live G: unsupported browser reported honestly",
    /not supported/.test(probeH.container.querySelector("#probe-err").textContent))
  probeH.unmount()
  entry.setGeolocation("ok", { lat: 28.2, lng: 83.98 }) // restore for any later sections

  // =========================================================================
  // OFFLINE ROUTE PACKS (increment 8) — real offlinePacks module on jsdom's
  // localStorage.
  // =========================================================================
  const packs = entry.offlinePacks
  const PACK_KEY = "nepal_nav_offline_packs_v1"
  const mkPack = (id, name) => ({
    id, destination_name: name, route: [{ lat: 27.7, lng: 85.3 }, { lat: 28.2, lng: 83.9 }],
    steps: [], distance_km: 200, calculated_at: new Date().toISOString(),
  })

  window.localStorage.setItem(PACK_KEY, "{corrupted json")
  check("packs: corrupted storage degrades to []", Array.isArray(packs.loadPacks()) && packs.loadPacks().length === 0)

  let list = packs.addPack([], mkPack(1, "Pokhara"))
  list = packs.addPack(list, mkPack(2, "Chitwan"))
  packs.persistPacks(list)
  const loaded = packs.loadPacks()
  check("packs: persist/load roundtrip", loaded.length === 2 && loaded[0].destination_name === "Chitwan")

  // same destination replaces (newest first), never duplicates
  list = packs.addPack(list, mkPack(3, "pokhara"))
  check("packs: same destination replaced case-insensitively",
    list.length === 2 && list[0].id === 3 && list[1].destination_name === "Chitwan")

  // cap at 5
  for (let i = 10; i < 16; i += 1) list = packs.addPack(list, mkPack(i, `Place ${i}`))
  check("packs: capped at 5, newest kept", list.length === 5 && list[0].id === 15)

  // finder
  check("packs: destination finder is case-insensitive",
    packs.findPackForDestination(list, "place 15")?.id === 15
    && packs.findPackForDestination(list, "Nowhere") === null
    && packs.findPackForDestination(list, "") === null)

  // removal + persistence of removal
  list = packs.removePack(list, 15)
  packs.persistPacks(list)
  check("packs: removal persists", packs.loadPacks().every((p) => p.id !== 15))

  // packs without a usable route are filtered out on load
  window.localStorage.setItem(PACK_KEY, JSON.stringify([{ id: 99, destination_name: "Broken", route: [] }, mkPack(100, "Good")]))
  const filtered = packs.loadPacks()
  check("packs: routeless entries filtered on load", filtered.length === 1 && filtered[0].id === 100)
  window.localStorage.removeItem(PACK_KEY)

  console.log(results.join("\n"))
  console.log(`\n${results.length - failures}/${results.length} passed`)
  process.exit(failures ? 1 : 0)
}

main().catch((e) => { console.error(e); process.exit(2) })
