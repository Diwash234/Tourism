import axios from "axios"

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1"

export const isGuestPreview = () => {
  try {
    return new URLSearchParams(window.location.search).get("as") === "traveller"
  } catch {
    return false
  }
}

const axiosClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  // Never let a request spin the UI forever: a hung backend/network errors
  // out after 20s with a catchable rejection instead of an endless spinner
  // (the browser default can hang for a minute or more). Slow operations
  // (media uploads) override this per-request with a longer timeout.
  timeout: 20000,
})

export const clearAuthStorage = () => {
  localStorage.removeItem("access")
  localStorage.removeItem("refresh")
  localStorage.removeItem("user")
}

// Attach access token to request if present (per-request only — never on
// axiosClient.defaults, which would leak a stale token after logout).
axiosClient.interceptors.request.use((config) => {
  if (isGuestPreview() || config._retryNoAuth) {
    if (config.headers) {
      delete config.headers.Authorization
      if (typeof config.headers.delete === "function") {
        config.headers.delete("Authorization")
      }
    }
    return config
  }
  const token = localStorage.getItem("access")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------------------------------------------------------------------------
// 401 handling: single-flight refresh, rotate-aware, with anonymous recovery.
//
// DRF rejects an invalid Authorization header with 401 *before* permission
// checks, so a stale token turns even public reads (destinations, hotels...)
// into 401s. Flow on 401:
//   1. one refresh attempt (shared by all concurrent 401s — never parallel,
//      the backend rotates+blacklists refresh tokens so racing refreshes
//      would blacklist each other)
//   2. refresh success  -> persist BOTH tokens (rotation!) and retry
//   3. refresh failure  -> clear session, retry the original request ONCE
//      without Authorization so public data still loads; only if that also
//      401s (genuinely protected) surface "session expired" and reject.
// ---------------------------------------------------------------------------
let isRefreshing = false
let queue = []

const notifySession = (kind) => {
  try {
    window.dispatchEvent(new CustomEvent(kind === "expired" ? "session-expired" : "session-downgraded"))
  } catch {
    /* non-browser environment */
  }
}

const retryWithoutAuth = (config) => {
  const cfg = { ...config, _retryNoAuth: true }
  if (cfg.headers) {
    delete cfg.headers.Authorization
    if (typeof cfg.headers.delete === "function") {
      cfg.headers.delete("Authorization")
    }
  }
  return axiosClient(cfg)
}

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const url = originalRequest?.url || ""

    // Network-level failure (no HTTP response at all — "connection
    // refused", DNS, dropped line, timeout). Browsers surface these as a
    // raw "Network Error" string, so pages often showed cryptic toasts.
    // Replace the message with an actionable explanation while keeping
    // the error object otherwise intact for logging/retry logic.
    // A request the page cancelled itself (superseded search/plan) is not a
    // connectivity problem — pass it through untouched.
    if (error?.code === "ERR_CANCELED" || error?.name === "CanceledError") {
      return Promise.reject(error)
    }
    if (status === undefined) {
      error.apiUnreachable = true
      if (error.code === "ECONNABORTED" || /timeout/i.test(String(error.message || ""))) {
        error.message =
          "The Tourism API took too long to respond. Please check your internet connection and try again."
      } else {
        error.message =
          "Couldn't reach the Tourism API (connection refused). Please check your internet connection — if you run this site locally, make sure the Django backend is running on port 8000."
      }
      return Promise.reject(error)
    }

    // Never refresh for the auth endpoints themselves or public config.
    const isAuthRoute =
      url.includes("/auth/token/refresh/") || url.includes("/auth/login/") || url.includes("/config/public/")

    if (status !== 401 || !originalRequest || isGuestPreview() || isAuthRoute) {
      return Promise.reject(error)
    }

    // Already retried anonymously -> genuinely protected: stop, no loops.
    if (originalRequest._retryNoAuth) {
      return Promise.reject(error)
    }

    const hadSession = !!localStorage.getItem("user")
    const refreshToken = localStorage.getItem("refresh")
    const sentAuth = !!(originalRequest.headers && originalRequest.headers.Authorization)

    // Settle a request after session loss: retry public reads anonymously.
    const settleAnonymously = (cfg) => {
      const isSafeRead = !cfg.method || ["get", "head", "options"].includes(String(cfg.method).toLowerCase())
      if (!sentAuth && !isSafeRead) return Promise.reject(error)
      return retryWithoutAuth(cfg).catch((retryError) => {
        if (retryError?.response?.status === 401 && hadSession) notifySession("expired")
        return Promise.reject(retryError)
      })
    }

    // No usable refresh token: drop the stale access token and recover
    // public data anonymously instead of dead-ending the page.
    if (!refreshToken || originalRequest._retry) {
      if (localStorage.getItem("access")) {
        clearAuthStorage()
        if (hadSession) notifySession("downgraded")
      }
      return settleAnonymously(originalRequest)
    }

    // A refresh is already in flight: park this request with it.
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject, config: originalRequest })
      })
    }

    originalRequest._retry = true
    isRefreshing = true
    try {
      const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
        refresh: refreshToken,
      })
      const newAccessToken = data?.access
      if (!newAccessToken) throw new Error("Token refresh response missing access token")
      localStorage.setItem("access", newAccessToken)
      // ROTATE_REFRESH_TOKENS is on: the old refresh token is blacklisted
      // after use, so the rotated one MUST be persisted or every future
      // refresh 401s.
      if (data?.refresh) localStorage.setItem("refresh", data.refresh)

      const queued = queue
      queue = []
      queued.forEach((p) => {
        p.config._retry = true
        p.config.headers = { ...(p.config.headers || {}), Authorization: `Bearer ${newAccessToken}` }
        axiosClient(p.config).then(p.resolve, p.reject)
      })

      originalRequest.headers = { ...(originalRequest.headers || {}), Authorization: `Bearer ${newAccessToken}` }
      return axiosClient(originalRequest)
    } catch (refreshError) {
      const queued = queue
      queue = []
      clearAuthStorage()
      // Parked requests each get the same anonymous-recovery treatment.
      queued.forEach((p) => {
        settleAnonymously(p.config).then(
          (res) => {
            if (hadSession) notifySession("downgraded")
            p.resolve(res)
          },
          (err) => p.reject(err)
        )
      })
      const settled = await settleAnonymously(originalRequest)
      if (hadSession) notifySession("downgraded")
      return settled
    } finally {
      isRefreshing = false
    }
  }
)

export default axiosClient
