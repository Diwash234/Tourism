/**
 * Service Worker for Nepal Tourism Platform
 *
 * Strategies:
 * - Cache-first for static assets (JS, CSS, images)
 * - Network-first for API calls with offline fallback
 * - Offline page fallback for navigation requests
 * - Background sync for form submissions
 */

const CACHE_NAME = "nepal-tourism-v1"
const STATIC_CACHE = "nepal-tourism-static-v1"
const API_CACHE = "nepal-tourism-api-v1"
const OFFLINE_URL = "/offline.html"

// Assets to precache on install
const PRECACHE_ASSETS = [
  "/",
  "/index.html",
  "/offline.html",
  "/manifest.json",
]

// ─── Install Event ───────────────────────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS)
    })
  )
  self.skipWaiting()
})

// ─── Activate Event ──────────────────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== STATIC_CACHE && name !== API_CACHE)
          .map((name) => caches.delete(name))
      )
    })
  )
  self.clients.claim()
})

// ─── Fetch Event ─────────────────────────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Skip non-GET requests for caching (but handle background sync)
  if (request.method !== "GET") {
    return
  }

  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith("http")) {
    return
  }

  // API calls: Network-first with cache fallback
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(request))
    return
  }

  // Static assets: Cache-first with network fallback
  if (
    url.pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/) ||
    url.pathname.startsWith("/assets/")
  ) {
    event.respondWith(cacheFirst(request))
    return
  }

  // Navigation requests: Network-first with offline fallback
  if (request.mode === "navigate") {
    event.respondWith(networkFirstWithOfflineFallback(request))
    return
  }

  // Default: Stale-while-revalidate
  event.respondWith(staleWhileRevalidate(request))
})

// ─── Caching Strategies ──────────────────────────────────────────────────────

/**
 * Cache-first strategy for static assets
 * Returns cached version if available, otherwise fetches from network
 */
async function cacheFirst(request) {
  const cached = await caches.match(request)
  if (cached) {
    return cached
  }

  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE)
      cache.put(request, response.clone())
    }
    return response
  } catch (err) {
    // Return offline fallback for navigations
    if (request.mode === "navigate") {
      return caches.match(OFFLINE_URL)
    }
    throw err
  }
}

/**
 * Network-first strategy for API calls
 * Tries network first, falls back to cache if offline
 */
async function networkFirst(request) {
  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(API_CACHE)
      cache.put(request, response.clone())
    }
    return response
  } catch (err) {
    const cached = await caches.match(request)
    if (cached) {
      return cached
    }
    throw err
  }
}

/**
 * Network-first with offline page fallback for navigations
 */
async function networkFirstWithOfflineFallback(request) {
  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE)
      cache.put(request, response.clone())
    }
    return response
  } catch (err) {
    const cached = await caches.match(request)
    if (cached) {
      return cached
    }
    return caches.match(OFFLINE_URL)
  }
}

/**
 * Stale-while-revalidate strategy
 * Returns cached version immediately, updates cache in background
 */
async function staleWhileRevalidate(request) {
  const cached = await caches.match(request)

  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        const cache = await caches.open(STATIC_CACHE)
        cache.put(request, response.clone())
      }
      return response
    })
    .catch(() => cached)

  return cached || fetchPromise
}

// ─── Background Sync ────────────────────────────────────────────────────────
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-forms") {
    event.waitUntil(syncFormData())
  }
})

async function syncFormData() {
  // Get pending form submissions from IndexedDB or localStorage
  // and retry them when back online
  const db = await openDB()
  const pending = await db.getAll("pendingForms")

  for (const form of pending) {
    try {
      await fetch(form.url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form.data),
      })
      await db.delete("pendingForms", form.id)
    } catch (err) {
      console.warn("Background sync failed for form:", form.id)
    }
  }
}

// ─── Push Notifications ──────────────────────────────────────────────────────
self.addEventListener("push", (event) => {
  if (!event.data) return

  const data = event.data.json()
  const options = {
    body: data.body,
    icon: "/icon-192x192.png",
    badge: "/badge-72x72.png",
    data: { url: data.url },
  }

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  )
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  const url = event.notification.data?.url || "/"
  event.waitUntil(
    self.clients.openWindow(url)
  )
})

// ─── Helper: Open IndexedDB ──────────────────────────────────────────────────
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("OfflineFormsDB", 1)
    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve(request.result)
    request.onupgradeneeded = (event) => {
      const db = event.target.result
      if (!db.objectStoreNames.contains("pendingForms")) {
        db.createObjectStore("pendingForms", { keyPath: "id", autoIncrement: true })
      }
    }
  })
}
