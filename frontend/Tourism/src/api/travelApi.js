import axiosClient from "./axiosClient";

/**
 * Travel planner API — real routes BETWEEN any two destinations.
 *
 *  plan:          GET /api/v1/navigation/travel-plan/
 *    ?origin=<slug|id|place|—>            (or origin_lat/origin_lng for GPS)
 *    &destination=<slug|id|place>
 *    &mode=driving|walking|cycling|hiking|motorcycle
 *    &alternatives=1
 *  travelBetween: GET /api/v1/navigation/travel-between/?from=<slug>&limit=24
 */
const travelApi = {
  plan: (params = {}) => axiosClient.get("/navigation/travel-plan/", { params }),
  travelBetween: (from, limit = 24) =>
    axiosClient.get("/navigation/travel-between/", { params: { from, limit } }),
};

export default travelApi;
