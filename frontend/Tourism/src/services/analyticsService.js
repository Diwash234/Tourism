import api from "./api"

export const analyticsService = {
  getStats: () => api.get("/admin/stats"),
  getUserTracking: () => api.get("/admin/user-tracking/"),
  getEmergencies: () => api.get("/admin/emergencies/"),
  resolveEmergency: (id) => api.post(`/admin/emergencies/${id}/resolve/`),
  getExpenseFeedbacks: () => api.get("/expense-feedback/"),
  getRiskFeedbacks: () => api.get("/risk-feedback/"),
}

export default analyticsService
