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
    )



}


export default destinationApi