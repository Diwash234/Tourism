import axiosClient from "./axiosClient"

// CONFIRMED WORKING as-is — no changes needed. All three now match real
// backend endpoints:
//   getNearbyPlaces -> GET /api/v1/nearby/places   (added: combines your
//                       Destination table + live OSM points)
//   getHospitals    -> GET /api/v1/nearby/hospitals
//   getPoliceStations -> GET /api/v1/nearby/police
const nearbyApi = {

  getNearbyPlaces: (params) =>
    axiosClient.get("/nearby/places", {
      params
    }),


  getHospitals: (params) =>
    axiosClient.get("/nearby/hospitals", {
      params
    }),


  getPoliceStations: (params) =>
    axiosClient.get("/nearby/police", {
      params
    }),


  // Kept for compatibility — navigationApi.js's getRoute does the same
  // thing; either works, this one's just redundant, not broken.
  getRoute: (payload) =>
    axiosClient.post("/navigation/route", payload)

}


export default nearbyApi