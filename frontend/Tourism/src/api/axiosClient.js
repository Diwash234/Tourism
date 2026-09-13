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
  // Safety net against 30-60s hangs: fast endpoints return in well under
  // this, and only a genuinely stalled server/AI call trips the timeout so
  // the caller rejects cleanly instead of leaving a frozen spinner.
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
  if (isGuestPreview()) {
    if (config.headers) delete config.headers.Authorization
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
  cfg.headers = { ...(config.headers || {}) }
  delete cfg.headers.Authorization
  return axiosClient(cfg)
}

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const url = originalRequest?.url || ""

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
      if (!sentAuth) return Promise.reject(error) // was never authed; nothing to strip
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
