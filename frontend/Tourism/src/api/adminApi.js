import axiosClient from "./axiosClient"

const adminApi = {
  getStats: () => axiosClient.get("/admin/stats"),
  getUsers: (params) => axiosClient.get("/admin/users", { params }),
  updateUserStatus: (id, payload) => axiosClient.put(`/admin/users/${id}/status`, payload),
  getDestinations: (params) => axiosClient.get("/admin/destinations", { params }),
  createDestination: (payload) => axiosClient.post("/admin/destinations", payload),
  updateDestination: (id, payload) => axiosClient.put(`/admin/destinations/${id}`, payload),
  deleteDestination: (id) => axiosClient.delete(`/admin/destinations/${id}`),
  getAlerts: (params) => axiosClient.get("/admin/alerts", { params }),
  createAlert: (payload) => axiosClient.post("/admin/alerts", payload),
}

export default adminApi