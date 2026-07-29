import axiosClient from "./axiosClient"


const chatbotApi = {

  sendMessage: (
    message,
    latitude = null,
    longitude = null,
    conversation_id = null
  ) => {

    return axiosClient.post(
      "/chatbot/message/",
      {
        message,
        latitude,
        longitude,
        conversation_id,
      }
    )

  },


  history: () => {

    return axiosClient.get(
      "/chatbot/history/"
    )

  },


}


export default chatbotApi
