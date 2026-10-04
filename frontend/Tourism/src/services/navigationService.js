import api from "./api"

export const navigationService = {
  getRoute: (payload) => api.post("/navigation/route", payload),
  // `radius` is kilometres — the backend reads `radius_km` (`radius` is
  // metres), so sending it here asked for a 0.025 m search every time.
  getNearbyPlaces: (lat, lng, radius_km) =>
    api.get("/nearby/places", { params: { lat, lng, radius_km } }),
  getNearbyHospitals: (lat, lng, radius_km) =>
    api.get("/nearby/hospitals", { params: { lat, lng, ...(radius_km != null ? { radius_km } : {}) } }),
  getNearbyPolice: (lat, lng, radius_km) =>
    api.get("/nearby/police", { params: { lat, lng, ...(radius_km != null ? { radius_km } : {}) } }),
  getCurrentWeather: (lat, lng) => api.get("/weather/current/", { params: { lat, lng } }),
}

export default navigationService
