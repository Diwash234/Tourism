import axiosClient from "./axiosClient"

const userApi = {
  // Profile
  getProfile: () =>
    axiosClient.get("/auth/profile/"),

  updateProfile: (payload) =>
    axiosClient.put("/auth/profile/", payload),


  // Password
  changePassword: (payload) =>
    axiosClient.put("/auth/change-password/", payload),


  // Favorites
  getFavorites: () =>
    axiosClient.get("/favorites/"),

  addFavorite: (destinationId) =>
    axiosClient.post(`/favorites/${destinationId}/`),

  removeFavorite: (destinationId) =>
    axiosClient.delete(`/favorites/${destinationId}/`),


  // History
  getHistory: () =>
    axiosClient.get("/history/"),


  // Notifications
  getNotifications: () =>
    axiosClient.get("/notifications/"),

  markNotificationRead: (id) =>
    axiosClient.put(`/notifications/${id}/mark_read/`),


  // Remove this unless you create a Django URL for it
  updateSettings: (payload) =>
    axiosClient.put("/auth/profile/", payload),
}

export default userApi