import axiosClient from "./axiosClient"

const destinationApi = {

  getAll: (params = {}) =>
    axiosClient.get("/destinations/", { params }),

  getDestinations: (params = {}) =>
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

  /** Lightweight autocomplete for search dropdown.
   *  Returns { data: [{ id, name, slug, cover_image_url, category_name, district }] }
   */
  autocomplete: (query, params = {}) =>
    axiosClient.get("/destinations/autocomplete/", {
      params: { q: query, limit: 8, type: "attraction", ...params },
    }),

  getImages: (slugOrId) =>
    axiosClient.get(`/destinations/${slugOrId}/images/`),

  discoverImages: (slugOrId) =>
    axiosClient.post(`/destinations/${slugOrId}/images/discover/`),

  refreshImages: (slugOrId) =>
    axiosClient.post(`/destinations/${slugOrId}/images/refresh/`),

  /** Mood-based recommendations
   *  params: { mood, days, limit }
   *  moods: relaxed, chill, adventure, romantic, family, spiritual, cultural,
   *         wildlife, trekking, hiking, scenic, photography, happy, excited,
   *         solitude, sad, energetic, winter, pilgrimage, lakeside, peaceful
   */
  moodRecommendations: (params = {}) =>
    axiosClient.get("/destinations/mood-recommendations/", { params }),

  getDistrictGallery: () => axiosClient.get("/gallery/districts/"),

}


export default destinationApi