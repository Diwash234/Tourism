import axiosClient from "./axiosClient"

const nearbyApi = {

  // Search places near current location
  getNearbyPlaces: (params) =>
    axiosClient.get("/nearby/places", {
      params
    }),


  // Search hospitals near current location
  getHospitals: (params) =>
    axiosClient.get("/nearby/hospitals", {
      params
    }),


  // Search police stations near current location
  getPoliceStations: (params) =>
    axiosClient.get("/nearby/police", {
      params
    }),


  // Only keep if backend has this endpoint
  getRoute: (payload) =>
    axiosClient.post("/navigation/route", payload)

}


export default nearbyApi