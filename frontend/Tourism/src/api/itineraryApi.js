import axiosClient from "./axiosClient"

// Rich, dataset-driven itinerary builder. The backend (Django
// /api/v1/ml/itinerary/ -> ML service /itinerary/build) plans a
// day-by-day trip from the OSM dataset using days, budget (NPR), travel
// style, travel type and interests, with route legs from the road graph.
// It's a pure function of its inputs, so the Itinerary page calls it on
// every form change (debounced) for continuous updates.
const itineraryApi = {
  // `config` may carry an AbortSignal to cancel a superseded plan request
  // (every form edit re-plans). The timeout defaults above the global default
  // because planning can legitimately take longer, and callers may override it.
  build: (payload, config = {}) =>
    axiosClient.post("/ml/itinerary/", payload, { timeout: 45000, ...config }),
  savePlan: (payload) => axiosClient.post("/travel-plans/", payload),
  listPlans: () => axiosClient.get("/travel-plans/"),
  getCuratedList: (params = {}) => axiosClient.get("/curated-itineraries/", { params }),
  getCuratedDetail: (slug, params = {}) => axiosClient.get(`/curated-itineraries/${slug}/`, { params }),
  loadCuratedPlanner: (slug, params = {}) =>
    axiosClient.get(`/curated-itineraries/${slug}/`, { params: { mode: "planner", ...params } }),
  compareCurated: (params = {}) => axiosClient.get("/curated-itineraries/compare/", { params }),
  getCuratedSafety: (slug) => axiosClient.get(`/curated-itineraries/${slug}/safety/`),
  getCuratedPacking: (slug) => axiosClient.get(`/curated-itineraries/${slug}/packing/`),
}

export default itineraryApi
