import axiosClient from "./axiosClient"

/**
 * NONE of these /admin/* endpoints exist on the backend yet — Django's
 * admin is only the built-in HTML site at /admin/, not a JSON API. If you
 * have an admin dashboard page using this file, that's why it's empty/
 * erroring across the board (this wasn't in the bug list you sent me, but
 * flagging it since it's a real gap).
 *
 * Two ways to actually make this work — tell me which you want:
 *   1. Build a real /api/v1/admin/* namespace on the backend (stats,
 *      user management, alert creation) — a genuine new feature.
 *   2. Point these at what already exists instead:
 *        - destinations CRUD -> already works via /destinations/ (staff
 *          users can POST/PUT/DELETE there directly, no /admin/ prefix needed)
 *        - alerts CRUD -> already works via /alerts/ the same way
 *        - user list/stats -> genuinely doesn't exist anywhere yet
 */
const adminApi = {
  getStats: () => axiosClient.get("/admin/stats"),
  getUsers: (params) => axiosClient.get("/admin/users", { params }),
  updateUserStatus: (id, payload) => axiosClient.put(`/admin/users/${id}/status`, payload),

  // These two would work today if you just drop the /admin prefix, since
  // staff users already have full write access to /destinations/ directly:
  getDestinations: (params) => axiosClient.get("/destinations/", { params }),
  createDestination: (payload) => axiosClient.post("/destinations/", payload),
  updateDestination: (id, payload) => axiosClient.put(`/destinations/${id}/`, payload),
  deleteDestination: (id) => axiosClient.delete(`/destinations/${id}/`),

  // Same here — /alerts/ already supports staff CRUD directly:
  getAlerts: (params) => axiosClient.get("/alerts/", { params }),
  createAlert: (payload) => axiosClient.post("/alerts/", payload),
}

export default adminApi