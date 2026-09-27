/* Nepal Yatra service worker.
 *
 * Offline scope is deliberately small and honest:
 *  - the app shell (index.html) and the hashed JS/CSS it has loaded;
 *  - a public allowlist of safety data a traveller may need without signal:
 *    national emergency hotlines, visa/permit/fee requirements, NRB exchange
 *    rates and NTB season guidance. These are network-first: a cached copy is
 *    used only when the network fails, and it is marked with X-NY-Offline so
 *    the UI can say it may be out of date.
 * Nothing user-specific (auth, bookings, plans) and no POST is ever cached.
 */
const VERSION = "ny-v1"
const SHELL = `${VERSION}-shell`
const ASSETS = `${VERSION}-assets`
const DATA = `${VERSION}-data`
const MAX_ASSETS = 150

const SHELL_URLS = ["/", "/manifest.webmanifest", "/favicon.svg", "/pwa/icon-192.png"]
const OFFLINE_DATA = [
  /^\/api\/v1\/emergency\/national-hotlines\/?$/,
  /^\/api\/v1\/travel-requirements\/?$/,
  /^\/api\/v1\/fx\/rates\/?$/,
  /^\/api\/v1\/season-guide\/?$/,
]

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_URLS)).then(() => self.skipWaiting()))
})

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => !k.startsWith(`${VERSION}-`)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

async function trim(cacheName, max) {
  const cache = await caches.open(cacheName)
  const keys = await cache.keys()
  for (let i = 0; i < keys.length - max; i += 1) await cache.delete(keys[i])
}

async function networkFirstData(request) {
  const cache = await caches.open(DATA)
  try {
    const response = await fetch(request)
    if (response.ok) await cache.put(request, response.clone())
    return response
  } catch (err) {
    // Vary (Cookie/Authorization) must not hide the offline copy; the fallback
    // ignores the query string (requirements carry fees for every nationality).
    const cached = (await cache.match(request, { ignoreVary: true })) || (await cache.match(request, { ignoreVary: true, ignoreSearch: true }))
    if (!cached) throw err
    const headers = new Headers(cached.headers)
    headers.set("X-NY-Offline", "1")
    return new Response(await cached.blob(), { status: 200, statusText: "OK (offline copy)", headers })
  }
}

async function navigation(request) {
  try {
    const response = await fetch(request)
    if (response.ok) (await caches.open(SHELL)).put("/", response.clone())
    return response
  } catch {
    const shell = await caches.match("/")
    return shell || new Response("<h1>You're offline</h1><p>Reconnect to load Nepal Yatra.</p>", { headers: { "Content-Type": "text/html" } })
  }
}

async function cacheFirstAsset(request) {
  const cached = await caches.match(request)
  if (cached) return cached
  const response = await fetch(request)
  if (response.ok) {
    const cache = await caches.open(ASSETS)
    await cache.put(request, response.clone())
    trim(ASSETS, MAX_ASSETS)
  }
  return response
}

self.addEventListener("fetch", (event) => {
  const { request } = event
  if (request.method !== "GET") return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  if (request.mode === "navigate") {
    event.respondWith(navigation(request))
    return
  }
  if (url.pathname.startsWith("/api/")) {
    if (OFFLINE_DATA.some((rx) => rx.test(url.pathname))) event.respondWith(networkFirstData(request))
    return // every other API call goes straight to the network
  }
  if (url.pathname.startsWith("/assets/") || url.pathname.startsWith("/pwa/")) {
    event.respondWith(cacheFirstAsset(request))
  }
})
