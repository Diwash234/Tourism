import axios from "axios"

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"

const axiosClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
})

// Attach access token to every request
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 -> try refresh token once, then retry original request
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

    if (status === 401 && !originalRequest._retry) {
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
        const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, {
          refreshToken,
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
        window.location.href = "/login"
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default axiosClient