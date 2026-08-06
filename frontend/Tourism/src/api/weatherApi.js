import axiosClient from "./axiosClient"

const weatherApi = {
  getCurrentWeather(params) {
    return axiosClient.get("/weather/current/", { params })
  },
}

export default weatherApi