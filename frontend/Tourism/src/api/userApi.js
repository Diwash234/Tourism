import axiosClient from "./axiosClient"

const userApi = {
  // Profile
  getProfile: () =>
    axiosClient.get("/auth/profile/"),

  updateProfile: (payload) =>
    axiosClient.put("/auth/profile/", payload),


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
    axiosClient.get("/favorites/"),

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
  markNotificationRead: (id) =>
    axiosClient.put(`/notifications/${id}/mark_read/`),


  // NOTE: there is currently no backend model for these preferences
  // (email/push/SMS notification toggles, currency). This call will
  // succeed (200) because the profile serializer silently ignores unknown
  // fields, but nothing is actually persisted. See Settings.jsx comment
  // for details — this needs a real backend UserSettings model to work.
  updateSettings: (payload) =>
    axiosClient.put("/auth/profile/", payload),
}

export default userApi