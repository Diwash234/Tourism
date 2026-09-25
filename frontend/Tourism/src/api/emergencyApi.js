import axiosClient from "./axiosClient"

const emergencyApi = {
  forDestination: (destinationRef, params = {}) =>
    axiosClient.get(`/destinations/${encodeURIComponent(destinationRef)}/emergency/`, { params }),
  nearby: (latitude, longitude, params = {}) =>
    axiosClient.get("/emergency/nearby/", { params: { latitude, longitude, ...params } }),
  nationalHotlines: () => axiosClient.get("/emergency/national-hotlines/"),
}

export default emergencyApi
