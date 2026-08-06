import axiosClient from "./axiosClient"

const recommendationApi = {
  getPersonalized() {
    return axiosClient.get("/recommendations/personalized")
  },

  getRecommendations(params) {
    return axiosClient.get("/recommendations/personalized", { params })
  },
}

export default recommendationApi