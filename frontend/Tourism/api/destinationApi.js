import axiosClient from "./axiosClient"

const destinationApi = {
  getAll: (params) => axiosClient.get("/destinations", { params }),
  getById: (id) => axiosClient.get(`/destinations/${id}`),
  getNearby: (params) => axiosClient.get("/destinations/nearby", { params }),
  getReviews: (id) => axiosClient.get(`/destinations/${id}/reviews`),
  addReview: (id, payload) => axiosClient.post(`/destinations/${id}/reviews`, payload),
  search: (query) => axiosClient.get("/destinations/search", { params: { q: query } }),
}

export default destinationApi