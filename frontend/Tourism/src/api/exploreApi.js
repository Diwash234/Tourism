import axiosClient from "./axiosClient"

// Traveller discovery endpoints (Django views_explore.py). Every value these
// return is either a real record or a derived fact that carries its basis
// and source; unknown values come back as null, never as a guess.
const exploreApi = {
  search: (q, config = {}) => axiosClient.get("/search/", { params: { q }, ...config }),
  discover: (params, config = {}) => axiosClient.get("/discover/", { params, ...config }),
  discoverOptions: () => axiosClient.get("/discover/options/"),
  seasonGuide: (month, destination) => axiosClient.get("/season-guide/", { params: { month, destination } }),
  decide: (params, config = {}) => axiosClient.get("/decide/", { params, ...config }),
  sentiment: (slugOrId) => axiosClient.get(`/destinations/${slugOrId}/sentiment/`),
  sharePlan: (planId, rotate = false) => axiosClient.post(`/travel-plans/${planId}/share/`, { rotate }),
  unsharePlan: (planId) => axiosClient.delete(`/travel-plans/${planId}/share/`),
  sharedPlan: (token) => axiosClient.get(`/shared-plans/${token}/`),
}

export default exploreApi
