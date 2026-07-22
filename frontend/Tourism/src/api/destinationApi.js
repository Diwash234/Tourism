import axiosClient from "./axiosClient"

const destinationApi = {

  getAll: (params = {}) =>
    axiosClient.get("/destinations/", { params }),


  getById: (slug, params = {}) =>
    axiosClient.get(`/destinations/${slug}/`, { params }),


  getEssentials: (slug, params = {}) =>
    axiosClient.get(`/destinations/${slug}/essentials/`, { params }),


  getNearby: (params = {}) =>
    axiosClient.get("/destinations/nearby/", { params }),


  // FIXED: the backend has no nested `/destinations/{slug}/reviews/`
  // route — reviews are a flat resource filtered by a `destination` query
  // param instead.
  getReviews: (slug, destinationId) =>
    axiosClient.get("/reviews/", { params: { destination: destinationId } }),


  // FIXED: same issue — POST to the flat /reviews/ endpoint with the
  // destination id in the body, not a nested URL.
  addReview: (slug, destinationId, payload) =>
    axiosClient.post("/reviews/", { ...payload, destination: destinationId }),


  search: (query) =>
    axiosClient.get("/destinations/", {
      params: {
        search: query
      }
    })

}


export default destinationApi