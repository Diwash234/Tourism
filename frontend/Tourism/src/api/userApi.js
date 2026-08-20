import axiosClient from "./axiosClient"

const userApi = {
  // Profile
  getProfile: () =>
    axiosClient.get("/auth/profile/"),

  getCapabilities: () => axiosClient.get("/auth/capabilities/"),

  updateProfile: (payload) =>
    axiosClient.put("/auth/profile/", payload),

  // NEW: the profile picture field is `profile_picture` (ImageField),
  // not `avatar` — Profile.jsx was reading a field that doesn't exist on
  // the backend at all, so the uploaded photo (if any) never showed.
  // Needs multipart, hence the separate method and header override
  // rather than reusing updateProfile (which sends JSON).
  uploadAvatar: (file) => {
    const formData = new FormData()
    formData.append("profile_picture", file)
    return axiosClient.patch("/auth/profile/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  },


  // Password
  changePassword: (payload) =>
    axiosClient.post("/auth/change-password/", payload),


  // Favorites
  // FIXED: the backend's FavoriteViewSet works like this —
  //   POST   /favorites/          body: { destination: <destinationId> }   (create)
  //   DELETE /favorites/{favId}/                                            (delete by the FAVORITE's own id, not the destination's id)
  // The old code POSTed to `/favorites/${destinationId}/` (a detail URL,
  // which only supports GET/PUT/PATCH/DELETE, never POST -> always 405)
  // and DELETEd `/favorites/${destinationId}/` (treating the destination's
  // id as if it were the favorite row's own id, which is usually wrong).
  getFavorites: () =>
    localStorage.getItem("access")
      ? axiosClient.get("/favorites/").catch(() => ({ data: [] }))
      : Promise.resolve({ data: [] }),

  addFavorite: (destinationId) =>
    axiosClient.post("/favorites/", { destination: destinationId }),

  // Needs the FAVORITE's own id (from a getFavorites() result's `.id`
  // field), not the destination's id. If you only have the destination id
  // on hand, look it up first:
  //   const { data } = await userApi.getFavorites();
  //   const fav = data.results.find(f => f.destination === destinationId);
  //   if (fav) await userApi.removeFavorite(fav.id);
  removeFavorite: (favoriteId) =>
    axiosClient.delete(`/favorites/${favoriteId}/`),


  // History
  getHistory: () =>
    axiosClient.get("/history/"),


  // Notifications
  getNotifications: () =>
    axiosClient.get("/notifications/"),

  // Backend now accepts both POST and PUT for this action, so this call
  // works as-is.
  markNotificationRead: (id) => axiosClient.put(`/notifications/${id}/mark_read/`),
  markNotificationUnread: (id) => axiosClient.put(`/notifications/${id}/mark_unread/`),
  markAllNotificationsRead: () => axiosClient.post("/notifications/mark_all_read/"),
  markAllNotificationsUnread: () => axiosClient.post("/notifications/mark_all_unread/"),
  deleteNotification: (id) => axiosClient.delete(`/notifications/${id}/`),
  getNotificationPreferences: () => axiosClient.get("/notification-preferences/"),
  updateNotificationPreferences: (payload) => axiosClient.patch("/notification-preferences/", payload),


  // Language options use database IDs when updating the profile.
  // preferred_language
  // on the backend is a ForeignKey to Language (expects the language's
  // numeric id, not a code string like "en"), so the dropdown needs the
  // real list of Language records to build valid options.
  getLanguages: () =>
    axiosClient.get("/languages/"),

  updateSettings: (payload) =>
    axiosClient.put("/auth/profile/", payload),

  // Packages Booking (with client-side fallback)
  bookPackage: async (payload) => {
    try {
      return await axiosClient.post("/packages/book/", payload)
    } catch {
      const existing = JSON.parse(localStorage.getItem("tourism_booked_packages") || "[]")
      const booked = { id: Date.now().toString(), ...payload, createdAt: new Date().toISOString(), status: "Confirmed" }
      localStorage.setItem("tourism_booked_packages", JSON.stringify([booked, ...existing]))
      return { data: booked }
    }
  },

  // Personal Details Management (with client-side fallback)
  getPersonalDetails: async () => {
    try {
      return await axiosClient.get("/user/personal-details/")
    } catch {
      const items = JSON.parse(localStorage.getItem("tourism_personal_details") || "[]")
      return { data: { items } }
    }
  },

  addPersonalDetails: async (payload) => {
    try {
      return await axiosClient.post("/user/personal-details/", payload)
    } catch {
      const items = JSON.parse(localStorage.getItem("tourism_personal_details") || "[]")
      const newItem = { id: Date.now().toString(), ...payload }
      localStorage.setItem("tourism_personal_details", JSON.stringify([newItem, ...items]))
      return { data: newItem }
    }
  },

  updatePersonalDetails: async (id, payload) => {
    try {
      return await axiosClient.put(`/user/personal-details/${id}/`, payload)
    } catch {
      const items = JSON.parse(localStorage.getItem("tourism_personal_details") || "[]")
      const updated = items.map((item) => (item.id === id ? { ...item, ...payload } : item))
      localStorage.setItem("tourism_personal_details", JSON.stringify(updated))
      return { data: updated.find((item) => item.id === id) || payload }
    }
  },

  deletePersonalDetails: async (id) => {
    try {
      return await axiosClient.delete(`/user/personal-details/${id}/`)
    } catch {
      const items = JSON.parse(localStorage.getItem("tourism_personal_details") || "[]")
      localStorage.setItem("tourism_personal_details", JSON.stringify(items.filter((item) => item.id !== id)))
      return { data: { success: true } }
    }
  },
}

export default userApi