import axiosClient from "./axiosClient"

const authApi = {
  login: (payload) => axiosClient.post("/auth/login/", payload),

  register: (payload) => axiosClient.post("/auth/register/", payload),

  forgotPassword: (payload) =>
    axiosClient.post("/auth/forgot-password/", payload),

  resetPassword: (payload) =>
    axiosClient.post("/auth/reset-password/", payload),

  refreshToken: (payload) =>
    axiosClient.post("/auth/token/refresh/", payload),

  // FIXED: was calling POST /auth/logout/ with NO body. The backend's
  // LogoutView requires `{ "refresh": "<token>" }` to blacklist it —
  // without it, every logout call returned 400 and the token was never
  // actually invalidated server-side.
  logout: () =>
    axiosClient.post("/auth/logout/", { refresh: localStorage.getItem("refresh") }),

  getCurrentUser: () => axiosClient.get("/auth/profile/"),
}

export default authApi