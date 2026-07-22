import api from "./axios"

const recommendationApi = {
  getPersonalized() {
    return api.get("/recommendations/personalized")
  },

  // FIXED: Recommendation.jsx calls `recommendationApi.getRecommendations()`,
  // which didn't exist on this object at all — calling an undefined
  // function throws immediately, crashing that page's whole effect before
  // any request could even fire. Added here as an alias for the same
  // endpoint. NOTE: the backend's recommendation endpoint doesn't support
  // filtering by `category` yet — the param is accepted but currently has
  // no effect server-side (safe to leave in for when that's added).
  getRecommendations(params) {
    return api.get("/recommendations/personalized", { params })
  },
}

export default recommendationApi