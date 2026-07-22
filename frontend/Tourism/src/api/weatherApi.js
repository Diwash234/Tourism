import api from "./axios"

// CONFIRMED WORKING as-is. Matches GET /api/v1/weather/current/?lat=&lng=
// (added on the backend specifically to match this call). Returns 503 if
// OPENWEATHER_API_KEY isn't set — that's a real "service unavailable",
// not a bug, so handle it as an error case, not empty data.
const weatherApi = {

  getCurrentWeather(params) {
    return api.get(
      "/weather/current/",
      {
        params
      }
    )
  }

}

export default weatherApi