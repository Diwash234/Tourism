import axiosClient from "./axiosClient";

const adminPanelApi = {
  getHotelAssignments: () => axiosClient.get("/admin-panel/hotel-assignments/"),
  assignHotel: (hotelId, adminId, notes) =>
    axiosClient.post("/admin-panel/hotel-assignments/", { hotel: hotelId, admin: adminId, notes }),
  removeAssignment: (id) => axiosClient.delete(`/admin-panel/hotel-assignments/${id}/`),
  getTasks: () => axiosClient.get("/admin-panel/tasks/"),
  createTask: (payload) => axiosClient.post("/admin-panel/tasks/", payload),
  updateTaskStatus: (id, status) =>
    axiosClient.patch(`/admin-panel/tasks/${id}/`, { status }),
  getDashboardStats: () => axiosClient.get("/admin-panel/dashboard-summary/"),

  // FIXED: PlaceApprovals.jsx already called these two methods, but
  // neither was ever defined here -- the page threw
  // "adminPanelApi.getPendingDestinations is not a function" the
  // moment an admin opened it. There's no dedicated backend
  // "pending destinations" endpoint, so this reuses the normal
  // destinations list (staff accounts see pending ones too, per
  // DestinationViewSet.get_queryset) and the real approve action.
  getPendingDestinations: () => axiosClient.get("/destinations/", { params: { page_size: 100 } }),
  approveDestination: (slug, status, reviewNote) =>
    axiosClient.post(`/destinations/${slug}/approve/`, { status, review_note: reviewNote || "" }),

  // ADDED -- Destination Media Manager triage list (see
  // admin_panel.views.DestinationsMissingImagesView).
  getDestinationsMissingImages: (page = 1) =>
    axiosClient.get("/admin-panel/destinations-missing-images/", { params: { page } }),

  // FIXED: UserManagement.jsx already called all four of these methods
  // and had a whole "backend endpoint not built yet" fallback UI ready
  // for exactly this situation -- none of them were defined here, and
  // nothing existed on the backend either (see
  // admin_panel.views.UserManagementViewSet, newly added).
  getUsers: (page = 1) => axiosClient.get("/admin-panel/users/", { params: { page, page_size: 100 } }),
  updateUserRole: (userId, role) => axiosClient.patch(`/admin-panel/users/${userId}/`, { role }),
  deactivateUser: (userId) => axiosClient.post(`/admin-panel/users/${userId}/deactivate/`),
  activateUser: (userId) => axiosClient.post(`/admin-panel/users/${userId}/activate/`),

  // ADDED -- lets an admin view a specific user's activity across
  // parts of the site that were previously invisible to admins
  // entirely. Favorite/VisitHistory/Budget viewsets used to hard-scope
  // to request.user with no staff override at all -- fixed on the
  // backend to accept ?user=<id> for staff. Reviews/Bookings were
  // already globally visible to staff, just never had a ?user filter
  // wired up on this side either.
  getUserFavorites: (userId) => axiosClient.get("/favorites/", { params: { user: userId, page_size: 50 } }),
  getUserVisitHistory: (userId) => axiosClient.get("/history/", { params: { user: userId, page_size: 50 } }),
  getUserBudgets: (userId) => axiosClient.get("/budgets/", { params: { user: userId, page_size: 50 } }),
  getUserReviews: (userId) => axiosClient.get("/reviews/", { params: { user: userId, page_size: 50 } }),
  getUserBookings: (userId) => axiosClient.get("/bookings/", { params: { user: userId, page_size: 50 } }),
};

export default adminPanelApi;