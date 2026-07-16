import axiosClient from "./axiosClient"

const translationApi = {

  translateText: (payload) => {
    return axiosClient.post(
      "/translate/",
      payload
    )
  }

}

export default translationApi