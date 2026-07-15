import axiosClient from "./axiosClient"

const authApi = {
  login: (payload) => axiosClient.post("/auth/login", payload),
  register: (payload) => axiosClient.post("/auth/register", payload),
  forgotPassword: (payload) => axiosClient.post("/auth/forgot-password", payload),
  resetPassword: (payload) => axiosClient.post("/auth/reset-password", payload),
  refreshToken: (payload) => axiosClient.post("/auth/refresh-token", payload),
  logout: () => axiosClient.post("/auth/logout"),
  getCurrentUser: () => axiosClient.get("/auth/me"),
}

export default authApi