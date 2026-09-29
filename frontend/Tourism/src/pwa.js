// Service-worker registration (production builds only; dev servers and
// Vite HMR must never be intercepted). After the worker is active, warm the
// offline allowlist and the emergency / before-you-travel page chunks while
// the browser is idle, so they work later without signal.

const OFFLINE_WARM_URLS = [
  "/api/v1/emergency/national-hotlines/",
  "/api/v1/travel-requirements/?nationality=foreign",
  "/api/v1/fx/rates/",
]

const whenIdle = (fn) => (window.requestIdleCallback ? window.requestIdleCallback(fn, { timeout: 8000 }) : setTimeout(fn, 4000))

export function registerServiceWorker() {
  if (!import.meta.env.PROD || typeof window === "undefined") return
  if (!("serviceWorker" in navigator) || !window.isSecureContext) return
  // Only same-origin API deployments can be cached by the worker.
  const apiBase = import.meta.env.VITE_API_BASE_URL || "/api/v1"
  const sameOriginApi = apiBase.startsWith("/")
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js", { scope: "/" })
      .then(() => navigator.serviceWorker.ready)
      .then(() => whenIdle(() => {
        if (navigator.connection?.saveData) return
        if (sameOriginApi) OFFLINE_WARM_URLS.forEach((url) => fetch(url, { credentials: "omit" }).catch(() => {}))
        import("./pages/Emergency").catch(() => {})
        import("./pages/BeforeYouTravel").catch(() => {})
      }))
      .catch(() => { /* offline support is progressive; the site works without it */ })
  })
}
