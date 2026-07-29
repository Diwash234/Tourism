import axiosClient from "./axiosClient"

// Talks to the existing tourist.HotelViewSet (GET /api/v1/hotels/).
// bookingApi.listHotels() only supports filtering by destination — this
// adds sorting/searching so a real Hotels page is possible without
// touching the backend.
const hotelApi = {
  list: (params = {}) => axiosClient.get("/hotels/", { params }),

  getById: (id) => axiosClient.get(`/hotels/${id}/`),

  // "Recommended" isn't a real backend action (see HotelViewSet) — this
  // approximates it client-side with ?ordering=-rating. If you want a
  // genuine backend-computed recommendation, add a @action to
  // HotelViewSet (see the backend notes in chat).
  recommended: (params = {}) =>
    axiosClient.get("/hotels/", { params: { ...params, ordering: "-rating" } }),

  byDestination: (destinationId, params = {}) =>
    axiosClient.get("/hotels/", { params: { ...params, destination: destinationId } }),

  // Dedicated search endpoint — confirmed to exist on the local backend
  // (not yet pushed to GitHub as of this file, which is why it wasn't
  // visible when this file was first checked against the repo). Returns
  // a richer shape than the plain HotelViewSet list (image_url,
  // destination_name), which is why HotelSearch.jsx below uses this
  // instead of hotelApi.list().
  search: (query, params = {}) =>
    axiosClient.get("/hotels/search/", { params: { ...params, query } }).then((res) => res.data),
}

export default hotelApi