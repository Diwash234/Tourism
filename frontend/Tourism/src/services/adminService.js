import api from "./api"

export const adminService = {
  getUsers: (params) => api.get("/admin/users", { params }),
  createUser: (payload) => api.post("/admin/users", payload),
  updateUser: (id, payload) => api.put(`/admin/users/${id}/`, payload),
  deleteUser: (id) => api.delete(`/admin/users/${id}/`),
  updateUserStatus: (id, payload) => api.put(`/admin/users/${id}/status`, payload),
  getPendingImages: () => api.get("/admin/pending-images/"),
  approveImage: (id) => api.post(`/admin/pending-images/${id}/`, { action: "approve" }),
  rejectImage: (id) => api.post(`/admin/pending-images/${id}/`, { action: "reject" }),
}

export default adminService
