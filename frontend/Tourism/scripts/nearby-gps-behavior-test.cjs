const { JSDOM } = require("jsdom")
const path = require("path")

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/",
  pretendToBeVisual: true,
})
const { window } = dom
window.matchMedia = () => ({
  matches: false,
  addEventListener() {},
  removeEventListener() {},
  addListener() {},
  removeListener() {},
})

global.window = window
global.document = window.document
Object.defineProperty(global, "navigator", { value: window.navigator, configurable: true })
global.HTMLElement = window.HTMLElement
global.SVGElement = window.SVGElement
global.Element = window.Element
global.Node = window.Node
global.Event = window.Event
global.CustomEvent = window.CustomEvent
global.MouseEvent = window.MouseEvent
global.getComputedStyle = window.getComputedStyle
global.requestAnimationFrame = window.requestAnimationFrame
global.cancelAnimationFrame = window.cancelAnimationFrame
global.localStorage = window.localStorage
global.IS_REACT_ACT_ENVIRONMENT = true
window.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = window.ResizeObserver
window.scrollTo = () => {}

const entry = require(path.resolve(__dirname, "../tests-nav/nearby-test-bundle.cjs"))
const { act } = entry

const check = (message, condition) => {
  console.log(`${condition ? "PASS" : "FAIL"}  ${message}`)
  if (!condition) process.exitCode = 1
}

async function settle() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 30))
  })
}

async function main() {
  localStorage.removeItem("ny_cached_position")
  entry.setGeolocation("success", { lat: 27.7172, lng: 85.324, accuracy: 8 })
  entry.setNearbyFixture({
    results: [
      {
        id: "hotel-1",
        name: "GPS Test Hostel",
        type: "hotel",
        category: "Hotel",
        latitude: 27.718,
        longitude: 85.325,
        distance_km: 0.15,
        source: "test",
      },
      {
        id: "hospital-1",
        name: "GPS Test Hospital",
        type: "hospital",
        category: "Hospital",
        latitude: 27.72,
        longitude: 85.326,
        distance_km: 0.4,
        source: "test",
      },
      {
        id: "store-1",
        name: "GPS Test Store",
        type: "store",
        category: "Store",
        latitude: 27.721,
        longitude: 85.327,
        distance_km: 0.55,
        source: "test",
      },
    ],
  })

  const page = entry.mountNearbyPage()
  await settle()
  await settle()

  const calls = entry.getNearbyCalls()
  check("GPS fix automatically requests nearby places without a search", calls.length > 0)
  check(
    "nearby request uses the current browser coordinates",
    calls[0]?.params?.lat === 27.7172 && calls[0]?.params?.lng === 85.324
  )
  check(
    "default nearby results include hotels, hospitals, and stores",
    ["GPS Test Hostel", "GPS Test Hospital", "GPS Test Store"].every((name) =>
      page.container.textContent.includes(name)
    )
  )
  check(
    "current GPS accuracy is shown",
    page.container.textContent.includes("±8 m accuracy")
  )
  const inAppRoute = page.container.querySelector('a[href*="/navigation?"]')
  const inAppRouteUrl = inAppRoute
    ? new URL(inAppRoute.getAttribute("href"), "http://localhost/")
    : null
  check(
    "in-app route preserves GPS origin and destination coordinates",
    inAppRouteUrl?.searchParams.get("origin") === "My Current Location" &&
      inAppRouteUrl?.searchParams.has("destLat") &&
      inAppRouteUrl?.searchParams.has("destLng")
  )
  const mapRoute = page.container.querySelector('a[href*="google.com/maps/dir"]')
  check(
    "external turn-by-turn route starts from the current GPS coordinates",
    mapRoute?.getAttribute("href")?.includes("origin=27.7172%2C85.324")
  )
  if (inAppRoute) {
    entry.setGeolocation("success", { lat: 27.7172, lng: 85.324, accuracy: 8 })
    const navigationPage = entry.mountNavigationPage(inAppRoute.getAttribute("href"))
    await settle()
    await settle()
    const routeRequest = entry.getNavigationCalls().at(-1)
    const routePayload =
      typeof routeRequest === "string" ? JSON.parse(routeRequest) : routeRequest
    check(
      "in-app navigation requests a GPS fix for current-location routes",
      routePayload?.start_latitude === 27.7172 &&
        routePayload?.start_longitude === 85.324
    )
    check(
      "in-app navigation routes to the nearby result's exact coordinates",
      routePayload?.end_latitude === 27.718 &&
        routePayload?.end_longitude === 85.325
    )
    navigationPage.unmount()
  } else {
    check("in-app navigation route request is available", false)
  }
  page.unmount()
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
}).finally(() => {
  window.close()
  process.exit(process.exitCode || 0)
})
