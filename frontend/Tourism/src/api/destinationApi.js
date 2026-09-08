import axiosClient from "./axiosClient"


const destinationApi = {


  // Get all destinations
  getAll: (params = {}) =>
    axiosClient.get("/destinations/", {
      params
    }),



  // Search destination autocomplete
  // Used for itinerary search bar
  // Example:
  // Arun -> Arun Valley
  // Butwal -> Butwal
  search: (query) =>
    axiosClient.get("/destinations/autocomplete/", {
      params: {
        q: query
      }
    }),



  // Get destination categories
  getCategories: (params = {}) =>
    axiosClient.get("/categories/", {
      params
    }),

  // ADDED -- staff category management (create/delete). Backend
  // already fully supports this (CategoryViewSet, IsAdminOrReadOnly,
  // auto-slugify on save) -- confirmed with a real POST before
  // building this UI, no backend changes needed.
  createCategory: (payload) => axiosClient.post("/categories/", payload),
  deleteCategory: (slug) => axiosClient.delete(`/categories/${slug}/`),



  // Get single destination details
  getById: (slug, params = {}) =>
    axiosClient.get(`/destinations/${slug}/`, {
      params
    }),



  // Destination essentials
  getEssentials: (slug, params = {}) =>
    axiosClient.get(
      `/destinations/${slug}/essentials/`,
      {
        params
      }
    ),



  // Translate destination
  translate: (slug, languageCode) =>
    axiosClient.post(
      `/destinations/${slug}/translate/`,
      {
        language_code: languageCode
      }
    ),



  // Nearby destinations
  getNearby: (params = {}) =>
    axiosClient.get(
      "/destinations/nearby/",
      {
        params
      }
    ),



  // Destination photos
  getPhotos: (slug, params = {}) =>
    axiosClient.get(
      `/destinations/${slug}/photos/`,
      {
        params
      }
    ),



  // Destination weather
  getWeather: (slug, params = {}) =>
    axiosClient.get(
      `/destinations/${slug}/weather/`,
      {
        params
      }
    ),



  // Reviews
  // Backend uses flat reviews endpoint
  getReviews: (slug, destinationId) =>
    axiosClient.get(
      "/reviews/",
      {
        params: {
          destination: destinationId
        }
      }
    ),



  // Add review
  addReview: (
    slug,
    destinationId,
    payload
  ) =>
    axiosClient.post(
      "/reviews/",
      {
        ...payload,
        destination: destinationId
      }
    ),


  // ADDED -- admin media management (Destination Media Manager).
  // Backend: DestinationViewSet.photos / .history in tourist/views.py.
  getPhotos: (slug) =>
    axiosClient.get(`/destinations/${slug}/photos/`),

  addPhoto: (slug, { externalUrl, caption, isCover }) =>
    axiosClient.post(`/destinations/${slug}/photos/`, {
      external_url: externalUrl,
      caption: caption || "",
      is_cover: !!isCover,
    }),

  deletePhoto: (slug, photoId) =>
    axiosClient.delete(`/destinations/${slug}/photos/`, {
      params: { photo_id: photoId },
    }),

  getHistory: (slug) =>
    axiosClient.get(`/destinations/${slug}/history/`),

  // ADDED -- admin "Add Destination" form. Unlike SubmitPlacePage.jsx
  // (tourist submissions -- auto-geolocated, held for review), this is
  // for staff who know a place's exact real coordinates and want it
  // live immediately. Backend (DestinationWriteSerializer.create())
  // already auto-approves and publishes when request.user.is_staff.
  create: (payload) => axiosClient.post("/destinations/", payload),


}


export default destinationApi