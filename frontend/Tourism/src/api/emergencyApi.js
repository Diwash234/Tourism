import axiosClient from "./axiosClient"

const emergencyApi = {
  forDestination: (destinationRef, params = {}) =>
    axiosClient.get(`/destinations/${encodeURIComponent(destinationRef)}/emergency/`, { params }),
  nearby: (latitude, longitude, params = {}) =>
    axiosClient.get("/emergency/nearby/", { params: { latitude, longitude, ...params } }),
}

export default emergencyApi
