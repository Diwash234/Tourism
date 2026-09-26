import axiosClient from "./axiosClient"

const budgetApi = {
  // The server owns the estimate and its source. A failed request must reach
  // the page so it can show an honest retry state rather than fabricated costs.
  estimate: (data, config = {}) => axiosClient.post("/ml/budget/", data, config),
  getSummary: () => axiosClient.get("/budget/summary/"),
}

export default budgetApi
