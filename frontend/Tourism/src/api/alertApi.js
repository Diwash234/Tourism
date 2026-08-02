import axiosClient from "./axiosClient"

// The three /admin/* methods that used to be here (getStats, getUsers,
// updateUserStatus) always 404'd -- Django's /admin/ is only the built-in
// HTML admin site, not a JSON API, and nothing in the frontend actually
// called them. Removed rather than built out, since no page depends on
// them. If you want a real user-management screen later, that's a new
// backend namespace to build deliberately, not a quick fix here.
const adminApi = {
  getDestinations: (params) => axiosClient.get("/destinations/", { params }),
  createDestination: (payload) => axiosClient.post("/destinations/", payload),
  updateDestination: (id, payload) => axiosClient.put(`/destinations/${id}/`, payload),
  deleteDestination: (id) => axiosClient.delete(`/destinations/${id}/`),

  getAlerts: (params) => axiosClient.get("/alerts/", { params }),
  createAlert: (payload) => axiosClient.post("/alerts/", payload),
}

export default adminApi