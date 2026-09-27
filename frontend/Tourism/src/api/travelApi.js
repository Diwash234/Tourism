import axiosClient from "./axiosClient"

// Official traveller data served by Django:
// - NRB exchange rates (Nepal Rastra Bank, dated)
// - visa / TIMS / permit / park & heritage fees transcribed from
//   immigration.gov.np and ntb.gov.np (each item carries its source URL)
const travelApi = {
  fxRates: () => axiosClient.get("/fx/rates/"),
  requirements: (nationality = "foreign") =>
    axiosClient.get("/travel-requirements/", { params: { nationality } }),
  destinationRequirements: (id, params = {}) =>
    axiosClient.get(`/travel-requirements/destination/${id}/`, { params }),

  // The distance, Getting There and Travel Planner cards all use this one
  // coordinate-first contract. It resolves real destination/origin records
  // and uses the configured OSRM provider when available; the backend labels
  // graph or straight-line fallbacks instead of pretending they are Google
  // Maps road data.
  plan: async (params = {}) => {
    const { data } = await axiosClient.post("/navigation/calculate/", {
      destination: params.destination,
      destination_name: params.destination_name,
      destination_id: params.destination_id,
      origin: params.origin,
      origin_name: params.origin_name,
      origin_lat: params.origin_lat,
      origin_lng: params.origin_lng,
      transport_mode: params.transport_mode || "Private Car / Taxi",
      mode: params.mode,
      alternatives: params.alternatives,
      waypoints: params.waypoints,
    })
    const confidence = String(data.confidence_level || "").toUpperCase()
    const grade = confidence === "ROUTED" ? "real-road"
      : confidence === "GRAPH_APPROXIMATION" ? "corridor-estimate" : "straight-line"
    const normalizeGeometry = (geometry) => {
      if (Array.isArray(geometry)) return geometry
      return geometry?.coordinates || []
    }
    const normalizeRoute = (route, routeGrade = grade) => {
      const distanceKm = route.distance_km ?? (route.distance_m == null ? null : Number(route.distance_m) / 1000)
      const durationMin = route.duration_min ?? (route.duration_s == null ? null : Number(route.duration_s) / 60)
      return {
        ...route,
        distance_km: distanceKm,
        distance_m: route.distance_m ?? (distanceKm == null ? null : distanceKm * 1000),
        duration_min: durationMin,
        geometry: normalizeGeometry(route.geometry),
        steps: route.steps || [],
        grade: route.grade || routeGrade,
        source: route.source || route.routing_engine || route.route_source || "straight_line_fallback",
        note: route.note || route.route_note || route.duration_note || "",
      }
    }
    const primary = normalizeRoute(data)
    return {
      data: {
        ...data,
        destination: {
          id: data.destination_id,
          slug: data.destination_slug,
          name: data.destination_name,
          latitude: data.destination_latitude,
          longitude: data.destination_longitude,
          city: data.destination_city,
        },
        origin: {
          name: data.origin_name,
          latitude: data.origin_latitude,
          longitude: data.origin_longitude,
        },
        straight_line_km: data.straight_line_km,
        primary,
        alternatives: (data.alternatives || []).map((route) => normalizeRoute(route)),
        modes: [],
      },
    }
  },
}

export default travelApi
