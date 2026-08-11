import api from "./api"

export const submissionService = {
  submitPlace: (formData) =>
    api.post("/destinations/", formData, { headers: { "Content-Type": "multipart/form-data" } }),

  getMySubmissions: () =>
    api.get("/destinations/my_submissions/"),

  getPendingSubmissions: () =>
    api.get("/admin/pending-places/"),

  approveSubmission: (id, payload) =>
    api.post(`/admin/pending-places/${id}/`, { action: "approve", ...payload }),

  rejectSubmission: (id, payload) =>
    api.post(`/admin/pending-places/${id}/`, { action: "reject", ...payload }),
}

export default submissionService
