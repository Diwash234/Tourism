import axiosClient from "./axiosClient"

// Rich, dataset-driven itinerary builder. The backend (Django
// /api/v1/ml/itinerary/ -> ML service /itinerary/build) plans a
// day-by-day trip from the OSM dataset using days, budget (NPR), travel
// style, travel type and interests, with route legs from the road graph.
// It's a pure function of its inputs, so the Itinerary page calls it on
// every form change (debounced) for continuous updates.
const itineraryApi = {
  build: (payload) => axiosClient.post("/ml/itinerary/", payload),
}

export default itineraryApi
