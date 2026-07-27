import axiosClient from "./axiosClient";

const adminPanelApi = {
  getHotelAssignments: () => axiosClient.get("/admin-panel/hotel-assignments/"),
  assignHotel: (hotelId, adminId, notes) =>
    axiosClient.post("/admin-panel/hotel-assignments/", { hotel: hotelId, admin: adminId, notes }),
  removeAssignment: (id) => axiosClient.delete(`/admin-panel/hotel-assignments/${id}/`),
  getTasks: () => axiosClient.get("/admin-panel/tasks/"),
  createTask: (payload) => axiosClient.post("/admin-panel/tasks/", payload),
  updateTaskStatus: (id, status) =>
    axiosClient.patch(`/admin-panel/tasks/${id}/`, { status }),
  getDashboardStats: () => axiosClient.get("/admin-panel/dashboard-summary/"),
};

export default adminPanelApi;
