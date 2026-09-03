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
})

// Attach access token to request if present
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

// Handle 401 -> try refresh token once safely
let isRefreshing = false
let queue = []

const processQueue = (error, token = null) => {
  queue.forEach((p) => (error ? p.reject(error) : p.resolve(token)))
  queue = []
}

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const url = originalRequest?.url || ""

    // Never refresh tokens for login, token refresh, or public endpoints
    const isAuthRoute = url.includes("/auth/token/refresh/") || url.includes("/auth/login/") || url.includes("/config/public/")

    if (status === 401 && !originalRequest._retry && !isGuestPreview() && !isAuthRoute) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          queue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return axiosClient(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = localStorage.getItem("refresh")
        if (!refreshToken) {
          localStorage.removeItem("access")
          localStorage.removeItem("refresh")
          localStorage.removeItem("user")
          return Promise.reject(error)
        }
        const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        })
        const newAccessToken = data.access
        localStorage.setItem("access", newAccessToken)
        axiosClient.defaults.headers.Authorization = `Bearer ${newAccessToken}`
        processQueue(null, newAccessToken)
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return axiosClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem("access")
        localStorage.removeItem("refresh")
        localStorage.removeItem("user")
        window.dispatchEvent(new Event("auth-logout"))
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default axiosClient
