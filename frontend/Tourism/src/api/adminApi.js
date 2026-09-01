import axiosClient from "./axiosClient"

const adminApi = {
  getStats: () => axiosClient.get("/admin/stats"),
  getReports: (params) => axiosClient.get("/admin/reports/", { params }),
  getRetentionPolicy: () => axiosClient.get("/admin/retention/"),
  updateRetentionPolicy: (payload) => axiosClient.patch("/admin/retention/", payload),
  runRetentionPolicy: (dry_run = true) => axiosClient.post("/admin/retention/", { dry_run }),
  getTravelServices: (params) => axiosClient.get("/admin/travel-services/", { params }),
  updateTravelServiceStatus: (payload) => axiosClient.patch("/admin/travel-services/", payload),
  getRestaurants: (params) => axiosClient.get("/restaurants/", { params }),
  getRestaurant: (id) => axiosClient.get(`/restaurants/${id}/`),
  createRestaurant: (payload) => axiosClient.post("/restaurants/", payload),
  updateRestaurant: (id, payload) => axiosClient.patch(`/restaurants/${id}/`, payload),
  getTransitRoutes: (params) => axiosClient.get("/transit-routes/", { params }),
  getTransitRoute: (id) => axiosClient.get(`/transit-routes/${id}/`),
  createTransitRoute: (payload) => axiosClient.post("/transit-routes/", payload),
  updateTransitRoute: (id, payload) => axiosClient.patch(`/transit-routes/${id}/`, payload),
  getTravelPlans: (params) => axiosClient.get("/travel-plans/", { params }),
  exportReports: (params) => axiosClient.get("/admin/reports/", { params: { ...params, format: "csv" }, responseType: "blob" }),
  globalSearch: (q, params = {}) => axiosClient.get("/admin/search/", { params: { q, ...params } }),
  getDatasets: (params) => axiosClient.get("/admin/datasets/", { params }),
  validateDatasetUpload: (formData) => axiosClient.post("/admin/datasets/", formData, { headers: { "Content-Type": "multipart/form-data" } }),
  confirmDatasetImport: (payload) => axiosClient.put("/admin/datasets/", payload),
  downloadDataset: (dataset) => axiosClient.get("/admin/datasets/", { params: { dataset, download: true }, responseType: "blob" }),
  getMediaLibrary: (params) => axiosClient.get("/admin/media-library/", { params }),
  uploadMediaLibrary: (payload) => axiosClient.post("/admin/media-library/", payload, { headers: { "Content-Type": "multipart/form-data" } }),
  getReviewModeration: (params) => axiosClient.get("/admin/review-moderation/", { params }),
  moderateReviews: (payload) => axiosClient.patch("/admin/review-moderation/", payload),
  updateMediaLibrary: (payload) => axiosClient.patch("/admin/media-library/", payload),
  deleteMediaLibrary: (id) => axiosClient.delete("/admin/media-library/", { data: { id } }),
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
  getHotels: (params) => axiosClient.get("/hotels/", { params }),
  createHotel: (payload) => axiosClient.post("/hotels/", payload),
  updateHotel: (id, payload) => axiosClient.patch(`/hotels/${id}/`, payload),
  uploadHotelImage: (id, payload) => axiosClient.patch(`/hotels/${id}/`, payload, { headers: { "Content-Type": "multipart/form-data" } }),
  deleteHotel: (id) => axiosClient.delete(`/hotels/${id}/`),
  getBookings: (params) => axiosClient.get("/bookings/", { params }),
  updateBooking: (id, payload) => axiosClient.patch(`/bookings/${id}/`, payload),
  getHotelReviews: (params) => axiosClient.get("/hotel-reviews/", { params }),
  deleteHotelReview: (id) => axiosClient.delete(`/hotel-reviews/${id}/`),
  getDestinationFeatures: (params) => axiosClient.get("/admin/destination-features/", { params }),
  getTranslations: (params) => axiosClient.get("/admin/destination-translations/", { params }),
  createTranslation: (payload) => axiosClient.post("/admin/destination-translations/", payload),
  updateTranslation: (id, payload) => axiosClient.patch(`/admin/destination-translations/${id}/`, payload),
  deleteTranslation: (id) => axiosClient.delete(`/admin/destination-translations/${id}/`),
  getCategories: (params) => axiosClient.get("/categories/", { params }),
  createCategory: (payload) => axiosClient.post("/categories/", payload),
  updateCategory: (id, payload) => axiosClient.patch(`/categories/${id}/`, payload),
  deleteCategory: (id) => axiosClient.delete(`/categories/${id}/`),
  createDestinationFeature: (payload) => axiosClient.post("/admin/destination-features/", payload),
  updateDestinationFeature: (id, payload) => axiosClient.patch(`/admin/destination-features/${id}/`, payload),
  deleteDestinationFeature: (id) => axiosClient.delete(`/admin/destination-features/${id}/`),
  createDestination: (payload) => axiosClient.post("/destinations/", payload),
  updateDestination: (id, payload) => axiosClient.put(`/destinations/${id}/`, payload),
  deleteDestination: (id) => axiosClient.delete(`/destinations/${id}/`),

  getAlerts: (params) => axiosClient.get("/alerts/", { params }),
  getRiskIncidents: (params) => axiosClient.get("/admin/risk-incidents/", { params }),
  createRiskIncident: (payload) => axiosClient.post("/admin/risk-incidents/", payload),
  updateRiskIncident: (id, payload) => axiosClient.patch(`/admin/risk-incidents/${id}/`, payload),
  deleteRiskIncident: (id) => axiosClient.delete(`/admin/risk-incidents/${id}/`),
  getCurrentHazards: (params) => axiosClient.get("/admin/current-hazards/", { params }),
  createCurrentHazard: (payload) => axiosClient.post("/admin/current-hazards/", payload),
  updateCurrentHazard: (id, payload) => axiosClient.patch(`/admin/current-hazards/${id}/`, payload),
  deleteCurrentHazard: (id) => axiosClient.delete(`/admin/current-hazards/${id}/`),
  getRiskObservations: (params) => axiosClient.get("/admin/risk-observations/", { params }),
  createRiskObservation: (payload) => axiosClient.post("/admin/risk-observations/", payload),
  updateRiskObservation: (id, payload) => axiosClient.patch(`/admin/risk-observations/${id}/`, payload),
  deleteRiskObservation: (id) => axiosClient.delete(`/admin/risk-observations/${id}/`),
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
  runUserAccessAction: (id, action, extra = {}) => axiosClient.post(`/admin/users/${id}/actions`, { action, ...extra }),
  exploreData: (params) => axiosClient.get("/admin/data-explorer/", { params }),
  getBranding: () => axiosClient.get("/admin/branding/"),
  updateBranding: (branding) => axiosClient.patch("/admin/branding/", { branding }),
  uploadBrandingAsset: (formData) => axiosClient.post("/admin/branding/", formData, { headers: { "Content-Type": "multipart/form-data" } }),
  deleteBrandingAsset: (kind) => axiosClient.delete("/admin/branding/", { data: { kind } }),
  getCMS: (resource, params = {}) => axiosClient.get("/admin/cms/", { params: { resource, ...params } }),
  runCMSAction: (payload) => axiosClient.patch("/admin/cms/", payload),
  getStaffWorkspace: (module = "dashboard") => axiosClient.get("/admin/staff-workspace/", { params: { module } }),
  runStaffWorkspaceAction: (payload) => axiosClient.post("/admin/staff-workspace/", payload),
  getStaffCapabilities: () => axiosClient.get("/admin/staff-capabilities/"),
  updateStaffCapabilities: (payload) => axiosClient.put("/admin/staff-capabilities/", payload),
  createCMS: (payload) => axiosClient.post("/admin/cms/", payload),
  updateCMS: (payload) => axiosClient.patch("/admin/cms/", payload),
  getInfrastructureSubmissions: (params) => axiosClient.get("/admin/infrastructure-submissions/", { params }),
  reviewInfrastructureSubmission: (id, payload) => axiosClient.post(`/admin/infrastructure-submissions/${id}/`, payload),
  getMarketplace: (params) => axiosClient.get("/admin/marketplace/", { params }),
  createMarketplace: (payload) => axiosClient.post("/admin/marketplace/", payload),
  updateMarketplace: (payload) => axiosClient.patch("/admin/marketplace/", payload),
  getEmergencyDirectory: (params) => axiosClient.get("/admin/emergency-directory/", { params }),
  createEmergencyDirectory: (payload) => axiosClient.post("/admin/emergency-directory/", payload),
  updateEmergencyDirectory: (payload) => axiosClient.patch("/admin/emergency-directory/", payload),
  getVisitorDesk: (params) => axiosClient.get("/admin/visitor-desk/", { params }),
  createVisitorNotice: (payload) => axiosClient.post("/admin/visitor-desk/", payload),
  updateVisitorNotice: (payload) => axiosClient.patch("/admin/visitor-desk/", payload),
  deleteVisitorNotice: (id) => axiosClient.delete("/admin/visitor-desk/", { data: { id }, params: { id } }),
  setFeaturedDestination: (destination_id, is_featured = true) => axiosClient.post("/admin/visitor-desk/", { action: "feature", destination_id, is_featured }),

  // Featured Destinations Content Publishing Studio API
  getFeaturedDestinations: (params) => axiosClient.get("/admin/featured-destinations/", { params }),
  getFeaturedDestination: (id) => axiosClient.get(`/admin/featured-destinations/${id}/`),
  createFeaturedDestination: (payload) => axiosClient.post("/admin/featured-destinations/", payload),
  updateFeaturedDestination: (id, payload) => axiosClient.patch(`/admin/featured-destinations/${id}/`, payload),
  deleteFeaturedDestination: (id) => axiosClient.delete(`/admin/featured-destinations/${id}/`),
  reorderFeaturedDestinations: (items) => axiosClient.post("/admin/featured-destinations/reorder/", { action: "reorder", items }),
  getPublicFeaturedDestinations: () => axiosClient.get("/featured-destinations/"),
  getServiceMedia: (params) => axiosClient.get("/admin/service-media/", { params }),
  uploadServiceMedia: (formData) => axiosClient.post("/admin/service-media/", formData, { headers: { "Content-Type": "multipart/form-data" } }),
  deleteServiceMedia: (payload) => axiosClient.delete("/admin/service-media/", { data: payload }),
  runMLDataPipeline: (payload) => axiosClient.post("/admin/ml-data-pipeline/", payload),
  getMLStatus: () => axiosClient.get("/admin/ml/status/"),
  getAdminNotifications: (params) => axiosClient.get("/admin/notifications/", { params }),
  broadcastNotification: (payload) => axiosClient.post("/admin/notifications/", payload),
  updateAdminNotifications: (payload) => axiosClient.patch("/admin/notifications/", payload),
  getFeedback: (params) => axiosClient.get("/admin/feedback", { params }),
  replyFeedback: (id, reply, is_internal = false) => axiosClient.post(`/admin/feedback/${id}/reply`, { reply, is_internal }),
  updateFeedbackThread: (id, payload) => axiosClient.patch(`/admin/feedback/${id}/reply`, payload),
  sendFeedback: (payload) => axiosClient.post("/feedback", payload, payload instanceof FormData ? { headers: { "Content-Type": "multipart/form-data" } } : undefined),

  // Admin destination detail (data, gallery, edit history)
  getAdminDestination: (id) => axiosClient.get(`/admin/destinations/${id}`),
  updateAdminDestination: (id, payload) => axiosClient.put(`/admin/destinations/${id}`, payload),
  fillAdminDestinationLocation: (id) => axiosClient.post(`/admin/destinations/${id}`, { action: "fill_location" }),
  addAdminDestinationImage: (id, payload) => axiosClient.post(`/admin/destinations/${id}/images`, payload, payload instanceof FormData ? { headers: { "Content-Type": "multipart/form-data" } } : undefined),
  setAdminDestinationCover: (id, payload) => axiosClient.patch(`/admin/destinations/${id}/images`, { ...payload, is_cover: true }),
  updateAdminDestinationImage: (id, payload) => axiosClient.patch(`/admin/destinations/${id}/images`, payload),
  deleteAdminDestinationImage: (id, imageId) => axiosClient.delete(`/admin/destinations/${id}/images`, { data: { image_id: imageId } }),
  getAdminDestinationVideos: (id) => axiosClient.get(`/admin/destinations/${id}/videos`),
  addAdminDestinationVideo: (id, payload) => axiosClient.post(`/admin/destinations/${id}/videos`, payload, payload instanceof FormData ? { headers: { "Content-Type": "multipart/form-data" } } : undefined),
  updateAdminDestinationVideo: (id, payload) => axiosClient.patch(`/admin/destinations/${id}/videos`, payload),
  deleteAdminDestinationVideo: (id, videoId) => axiosClient.delete(`/admin/destinations/${id}/videos`, { data: { video_id: videoId } }),

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
