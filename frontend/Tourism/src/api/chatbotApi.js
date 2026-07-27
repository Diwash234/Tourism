import axiosClient from "./axiosClient";

const chatbotApi = {

  sendMessage: (
    message,
    latitude,
    longitude,
    conversation_id = null
  ) =>
    axiosClient.post(
      "/chatbot/message/",
      {
        message,
        latitude,
        longitude,
        conversation_id
      }
    ),


  history: () =>
    axiosClient.get("/chatbot/history/"),

};


export default chatbotApi;

