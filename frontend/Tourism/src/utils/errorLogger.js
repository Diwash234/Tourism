/**
 * frontend/Tourism/src/utils/errorLogger.js
 *
 * Lightweight frontend error reporter. Sends JS errors, unhandled promise
 * rejections, and explicit report() calls to the backend audit endpoint
 * /api/v1/audit/report-error/ so every React crash shows up in the admin
 * Diagnostics Center alongside backend exceptions.
 *
 * - Deduplicates identical errors within 60s (client-side)
 * - Attaches the current route, user agent, recent X-Request-Id, and any
 *   extra context you supply
 * - Fire-and-forget (never throws; fails silently if the API is down)
 */
const REPORT_URL = "/api/v1/audit/report-error/"
const recentFp = new Map() // fingerprint -> lastSent timestamp

const fingerprint = (name, message) =>
  `${name}|${String(message || "").slice(0, 120)}`

const getRoute = () => {
  try {
    return window.location.pathname + window.location.search
  } catch {
    return ""
  }
}

const getRequestId = () => {
  try {
    return window.__LAST_REQUEST_ID__ || ""
  } catch {
    return ""
  }
}

const send = (payload) => {
  try {
    // Use sendBeacon when available so errors reported during unload still ship
    const body = JSON.stringify(payload)
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" })
      const ok = navigator.sendBeacon(REPORT_URL, blob)
      if (ok) return
    }
    fetch(REPORT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
      // Do NOT rely on credentials here; anonymous reports are accepted
      credentials: "omit",
    }).catch(() => {})
  } catch {
    // swallow - reporting must never throw
  }
}

/**
 * Report an error to the backend.
 * @param {Error|string} err
 * @param {object} extra  optional extra fields (component, route, etc.)
 */
export function reportError(err, extra = {}) {
  try {
    const name = (err && err.name) || extra.name || "FrontendError"
    const message =
      (err && err.message) || (typeof err === "string" ? err : "Unknown error")
    const stack = (err && err.stack) || extra.stack || ""
    const fp = fingerprint(name, message)
    const now = Date.now()
    if (recentFp.has(fp) && now - recentFp.get(fp) < 60_000) return
    recentFp.set(fp, now)

    send({
      name,
      message: String(message).slice(0, 4000),
      stack: String(stack).slice(0, 8000),
      component: extra.component || "",
      url: window.location.href,
      route: extra.route || getRoute(),
      request_id: extra.requestId || getRequestId(),
      extra: {
        userAgent: navigator.userAgent,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        language: navigator.language,
        online: navigator.onLine,
        ...(extra.extra || {}),
      },
    })
  } catch {
    /* never throw */
  }
}

/** Install global handlers. Call once at app startup. */
export function installGlobalErrorHandlers() {
  if (typeof window === "undefined") return
  window.addEventListener("error", (event) => {
    const err = event.error ||
      new Error(`${event.message} @ ${event.filename}:${event.lineno}`)
    reportError(err, {
      extra: { filename: event.filename, lineno: event.lineno, colno: event.colno },
    })
  })
  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason
    const err = reason instanceof Error ? reason : new Error(String(reason))
    reportError(err, { name: "UnhandledPromiseRejection" })
  })
}
