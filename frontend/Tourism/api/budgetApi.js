import axiosClient from "./axiosClient"

const budgetApi = {
  estimate: (payload) => axiosClient.post("/budget/estimate", payload),
  getSummary: () => axiosClient.get("/budget/summary"),
  getHistory: () => axiosClient.get("/budget/history"),
}

export default budgetApi