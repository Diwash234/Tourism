import axiosClient from "./axiosClient"

const weatherApi = {
  getCurrentWeather: (params) => axiosClient.get("/weather/current", { params }),
}

export default weatherApi