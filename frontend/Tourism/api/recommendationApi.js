import axiosClient from "./axiosClient"

const recommendationApi = {
  getRecommendations: (params) => axiosClient.get("/recommendations", { params }),
  getPersonalized: () => axiosClient.get("/recommendations/personalized"),
}

export default recommendationApi