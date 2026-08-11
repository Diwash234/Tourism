import api from "./api"

export const navigationService = {
  getRoute: (payload) => api.post("/navigation/route", payload),
  getNearbyPlaces: (lat, lng, radius) => api.get("/nearby/places", { params: { lat, lng, radius } }),
  getNearbyHospitals: (lat, lng) => api.get("/nearby/hospitals", { params: { lat, lng } }),
  getNearbyPolice: (lat, lng) => api.get("/nearby/police", { params: { lat, lng } }),
  getCurrentWeather: (lat, lng) => api.get("/weather/current/", { params: { lat, lng } }),
}

export default navigationService
