import axiosClient from "./axiosClient"

const adminApi = {
  getStats: () => axiosClient.get("/admin/stats"),
  getUsers: (params) => axiosClient.get("/admin/users", { params }),
  createUser: (payload) => axiosClient.post("/admin/users", payload),
  updateUser: (id, payload) => axiosClient.put(`/admin/users/${id}/`, payload),
  updateUserStatus: (id, payload) => axiosClient.put(`/admin/users/${id}/status`, payload),
  deleteUser: (id) => axiosClient.delete(`/admin/users/${id}/`),

  getUserTracking: () => axiosClient.get("/admin/user-tracking/"),

  getPendingPlaces: () => axiosClient.get("/admin/pending-places/"),
  approvePlace: (id, payload = {}) => axiosClient.post(`/admin/pending-places/${id}/`, { action: "approve", ...payload }),
  rejectPlace: (id, payload = {}) => axiosClient.post(`/admin/pending-places/${id}/`, { action: "reject", ...payload }),

  getPendingImages: () => axiosClient.get("/admin/pending-images/"),
  approveImage: (id) => axiosClient.post(`/admin/pending-images/${id}/`, { action: "approve" }),
  rejectImage: (id) => axiosClient.post(`/admin/pending-images/${id}/`, { action: "reject" }),

  getEmergencies: () => axiosClient.get("/admin/emergencies/"),
  resolveEmergency: (id) => axiosClient.post(`/admin/emergencies/${id}/resolve/`),

  getExpenseFeedbacks: () => axiosClient.get("/expense-feedback/"),
  submitExpenseFeedback: (payload) => axiosClient.post("/expense-feedback/", payload),

  getRiskFeedbacks: () => axiosClient.get("/risk-feedback/"),
  submitRiskFeedback: (payload) => axiosClient.post("/risk-feedback/", payload),

  getDestinations: (params) => axiosClient.get("/destinations/", { params }),
  createDestination: (payload) => axiosClient.post("/destinations/", payload),
  updateDestination: (id, payload) => axiosClient.put(`/destinations/${id}/`, payload),
  deleteDestination: (id) => axiosClient.delete(`/destinations/${id}/`),

  getAlerts: (params) => axiosClient.get("/alerts/", { params }),
  createAlert: (payload) => axiosClient.post("/alerts/", payload),

  // Place Intelligence & Mass Discovery API
  getDiscoveryHealthReport: () => axiosClient.get("/admin/discovery/health-report/"),
  getDiscoveryStats: () => axiosClient.get("/admin/discovery/stats/"),
  getCandidates: (params) => axiosClient.get("/admin/discovery/candidates/", { params }),
  runDiscoveryBatch: (payload) => axiosClient.post("/admin/discovery/run-batch/", payload),
  candidateAction: (id, payload) => axiosClient.post(`/admin/discovery/candidates/${id}/action/`, payload),
  candidateBulkAction: (payload) => axiosClient.post("/admin/discovery/bulk-action/", payload),
}

export default adminApi
