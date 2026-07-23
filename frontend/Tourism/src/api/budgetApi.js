import axiosClient from "./axiosClient"

// CONFIRMED WORKING as-is:
//   estimate()   -> POST /api/v1/ml/budget/ — the backend was updated to
//                   accept exactly what BudgetEstimator.jsx sends
//                   ({destination: "<free text name>", style: "standard", ...})
//                   and its response is now flattened to {total, accommodation,
//                   food, transport, activities} matching what that page reads.
//   getSummary() -> GET /api/v1/budget/summary/ — backend now accepts
//                   this exact URL (with the trailing slash) too.
const budgetApi = {

  estimate: (data) =>
    axiosClient.post(
      "/ml/budget/",
      data
    ),

  getSummary: () =>
    axiosClient.get("/budget/summary/")

}

export default budgetApi

export const estimateBudget = (payload) =>
  axiosClient.post("/api/ml/budget/estimate/", payload)