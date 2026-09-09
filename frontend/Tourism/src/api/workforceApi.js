import axiosClient from "./axiosClient"

/**
 * Tourism Workforce platform APIs (guides, applications, verification center).
 * Backend enforces auth + capability + scope on every call.
 */
const workforceApi = {
  // Public
  guides: (params = {}) => axiosClient.get("/workforce/guides/", { params }),
  guide: (id) => axiosClient.get(`/workforce/guides/${id}/`),

  // Guide's own workspace
  myGuideProfile: () => axiosClient.get("/workforce/guide-profile/"),
  saveGuideProfile: (payload) => axiosClient.put("/workforce/guide-profile/", payload),
  myApplications: () => axiosClient.get("/workforce/guide-applications/"),
  applyAsGuide: (payload) => axiosClient.post("/workforce/guide-applications/", payload),

  // Verification center (admin/staff with marketplace capability)
  applications: (status = "") =>
    axiosClient.get("/workforce/admin/applications/", status ? { params: { status } } : {}),
  applicationAction: (id, action, note = "") =>
    axiosClient.post(`/workforce/admin/applications/${id}/action/`, { action, note }),
  guideAction: (id, action, note = "") =>
    axiosClient.post(`/workforce/admin/guides/${id}/action/`, { action, note }),
}

export default workforceApi
