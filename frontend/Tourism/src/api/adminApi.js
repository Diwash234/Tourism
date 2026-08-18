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
  submitExpenseFeedback: async (payload) => {
    try {
      return await axiosClient.post("/expense-feedback/", payload)
    } catch {
      const list = JSON.parse(localStorage.getItem("tourism_expense_feedback") || "[]")
      const created = { id: Date.now().toString(), ...payload, createdAt: new Date().toISOString() }
      localStorage.setItem("tourism_expense_feedback", JSON.stringify([created, ...list]))
      return { data: created }
    }
  },

  getRiskFeedbacks: () => axiosClient.get("/risk-feedback/"),
  submitRiskFeedback: async (payload) => {
    try {
      return await axiosClient.post("/risk-feedback/", payload)
    } catch {
      const list = JSON.parse(localStorage.getItem("tourism_risk_feedback") || "[]")
      const created = { id: Date.now().toString(), ...payload, createdAt: new Date().toISOString() }
      localStorage.setItem("tourism_risk_feedback", JSON.stringify([created, ...list]))
      return { data: created }
    }
  },

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

  // Multi-Source Image Acquisition & Provenance Pipeline API
  getDestinationImages: (slugOrId) => axiosClient.get(`/destinations/${slugOrId}/images/`),
  discoverDestinationImages: (slugOrId) => axiosClient.post(`/destinations/${slugOrId}/images/discover/`),
  refreshDestinationImages: (slugOrId) => axiosClient.post(`/destinations/${slugOrId}/images/refresh/`),
  setDestinationCover: (slugOrId, imageId) => axiosClient.post(`/destinations/${slugOrId}/images/${imageId}/set-cover/`),

  // Free web image search + save (Wikimedia / DuckDuckGo / Openverse)
  fetchWebImages: (destination, num = 12) =>
    axiosClient.post("/admin/fetch-images/", { destination, num }),
  generateAIImages: (destination, num = 12) =>
    axiosClient.post("/admin/generate-ai-images/", { destination, num }),
  deleteDestinationImage: (id) => axiosClient.delete(`/admin/images/${id}`),

  // Users + verification + feedback
  getUserDetail: (id) => axiosClient.get(`/admin/users/${id}/`),
  updateUser: (id, payload) => axiosClient.patch(`/admin/users/${id}/`, payload),
  sendVerification: (id, payload) => axiosClient.post(`/admin/users/${id}/send-verification`, payload),
  getInfrastructureSubmissions: (params) => axiosClient.get("/admin/infrastructure-submissions/", { params }),
  reviewInfrastructureSubmission: (id, payload) => axiosClient.post(`/admin/infrastructure-submissions/${id}/`, payload),
  runMLDataPipeline: (payload) => axiosClient.post("/admin/ml-data-pipeline/", payload),
  getFeedback: (params) => axiosClient.get("/admin/feedback", { params }),
  replyFeedback: (id, reply) => axiosClient.post(`/admin/feedback/${id}/reply`, { reply }),
  sendFeedback: (payload) => axiosClient.post("/feedback", payload),

  // Admin destination detail (data, gallery, edit history)
  getAdminDestination: (id) => axiosClient.get(`/admin/destinations/${id}`),
  updateAdminDestination: (id, payload) => axiosClient.put(`/admin/destinations/${id}`, payload),
  addAdminDestinationImage: (id, payload) => axiosClient.post(`/admin/destinations/${id}/images`, payload),
  setAdminDestinationCover: (id, payload) => axiosClient.patch(`/admin/destinations/${id}/images`, payload),
  deleteAdminDestinationImage: (id, imageId) => axiosClient.delete(`/admin/destinations/${id}/images`, { data: { image_id: imageId } }),

  // Diagnostics / Audit / Health (new backend apps)
  getAuditSummary: () => axiosClient.get("/audit/logs/summary/"),
  getAuditLogs: (params) => axiosClient.get("/audit/logs/", { params }),
  getErrors: (params) => axiosClient.get("/audit/errors/", { params }),
  acknowledgeError: (id, payload) => axiosClient.post(`/audit/errors/${id}/acknowledge/`, payload || {}),
  bulkResolveErrors: (ids, note = "") => axiosClient.post("/audit/errors/bulk-resolve/", { ids, resolution_note: note }),
  getHealthSamples: () => axiosClient.get("/audit/health/"),
  getLatestHealthSample: () => axiosClient.get("/audit/health/latest/"),
  runHealthCheck: () => axiosClient.get("/system/health/full/"),
  writeHealthSample: () => axiosClient.post("/system/health/sample/"),
}

export default adminApi
