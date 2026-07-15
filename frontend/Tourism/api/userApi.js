import axiosClient from "./axiosClient"

const userApi = {
  getProfile: () => axiosClient.get("/users/profile"),
  updateProfile: (payload) => axiosClient.put("/users/profile", payload),
  changePassword: (payload) => axiosClient.put("/users/change-password", payload),
  getFavorites: () => axiosClient.get("/users/favorites"),
  addFavorite: (destinationId) => axiosClient.post(`/users/favorites/${destinationId}`),
  removeFavorite: (destinationId) => axiosClient.delete(`/users/favorites/${destinationId}`),
  getHistory: () => axiosClient.get("/users/history"),
  getNotifications: () => axiosClient.get("/users/notifications"),
  markNotificationRead: (id) => axiosClient.put(`/users/notifications/${id}/read`),
  updateSettings: (payload) => axiosClient.put("/users/settings", payload),
}

export default userApi