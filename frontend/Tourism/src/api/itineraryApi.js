import axiosClient from "./axiosClient"

const itineraryApi = {

  createItinerary(data) {
    return axiosClient.post(
      "/itinerary/",
      data
    )
  }

}

export default itineraryApi