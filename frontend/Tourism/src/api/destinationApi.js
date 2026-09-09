import axiosClient from "./axiosClient"

const destinationApi = {

  getAll: (params = {}) =>
    axiosClient.get("/destinations/", { params }),

  getDestinations: (params = {}) =>
    axiosClient.get("/destinations/", { params }),

  // All destinations within radius_km of a point, nearest-first, paginated,
  // each row annotated with distance_km (straight-line).
  getNearbyDestinations: (params = {}) =>
    axiosClient.get("/destinations/nearby/", { params }),

  // Coordinate-first nearby POIs (user location → real-world places, spec §2)
  getPOIsByCoords: (params = {}) =>
    axiosClient.get("/nearby/pois/", { params }),

  // Real on-the-ground places (hotels/hospitals/temples/viewpoints/…) around a
  // destination, straight from OpenStreetMap via the backend proxy.
  getNearbyPOIs: (slugOrId, params = {}) =>
    axiosClient.get(`/destinations/${slugOrId}/nearby-pois/`, { params }),


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

  // Alias matching callers that use destinationApi.nearby(lat, lng, opts).
  // Backend /destinations/nearby/ expects latitude, longitude, radius_km.
  nearby: (lat, lng, params = {}) =>
    axiosClient.get("/destinations/nearby/", {
      params: {
        latitude: lat,
        longitude: lng,
        radius_km: params.radius_km ?? 250,
        page: params.page,
        limit: params.limit,
      },
    }),


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

  /** User place submission — POST multipart to the real /destinations/ endpoint.
   *  CanSubmitPlace lets any authenticated user submit; `cover_image` travels in
   *  the same request (see DestinationWriteSerializer). SubmitPlacePage and
   *  LocalDashboard both use this — previously SubmitPlacePage called
   *  destinationApi.submit() which did not exist on this wrapper. */
  submit: (formData) => axiosClient.post("/destinations/", formData),

  /** The requesting user's own submissions, incl. pending/rejected
   *  (backend action: DestinationViewSet.my_submissions). Paginated. */
  getMySubmissions: (params = {}) =>
    axiosClient.get("/destinations/my_submissions/", { params }),

  /** Submitter (while pending) or staff can delete a submission. */
  deleteSubmission: (slugOrId) =>
    axiosClient.delete(`/destinations/${slugOrId}/`),

  getFeaturedGallery: () => axiosClient.get("/gallery/featured/"),
  getDistrictGallery: () => axiosClient.get("/gallery/districts/"),
  discoverNepal: () => axiosClient.get("/discover-nepal/"),

}


export default destinationApi