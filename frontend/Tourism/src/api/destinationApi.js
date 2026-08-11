import axiosClient from "./axiosClient"

const destinationApi = {

  getAll: (params = {}) =>
    axiosClient.get("/destinations/", { params }),


  // NEW: needed to find the "Culture & Heritage" / "Local Experience"
  // categories used by NepalExperienceSection — the CategoryViewSet was
  // already registered on the backend (router.register("categories", ...)
  // in tourist/urls.py), just never called from the frontend before.
  getCategories: (params = {}) =>
    axiosClient.get("/categories/", { params }),


  getById: (slug, params = {}) =>
    axiosClient.get(`/destinations/${slug}/`, { params }),


  getEssentials: (slug, params = {}) =>
    axiosClient.get(`/destinations/${slug}/essentials/`, { params }),


  translate: (slug, languageCode) =>
    axiosClient.post(`/destinations/${slug}/translate/`, { language_code: languageCode }),


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
    }),

  searchDiscover: (query) =>
    axiosClient.get("/destinations/search-discover/", {
      params: { query }
    }),

  researchDestination: (query) =>
    axiosClient.post("/destinations/research/", { query }),

}


export default destinationApi