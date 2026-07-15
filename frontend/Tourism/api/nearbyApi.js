import axiosClient from "./axiosClient"

const nearbyApi = {
  getNearbyPlaces: (params) => axiosClient.get("/nearby/places", { params }),
  getHospitals: (params) => axiosClient.get("/nearby/hospitals", { params }),
  getPoliceStations: (params) => axiosClient.get("/nearby/police", { params }),
  getRoute: (payload) => axiosClient.post("/navigation/route", payload),
}

export default nearbyApi