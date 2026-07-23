import axiosClient from "./axiosClient";

const chatbotApi = {
  sendMessage: (message, conversation_id = null) =>
    axiosClient.post("/chatbot/message/", { message, conversation_id }),
  history: () => axiosClient.get("/chatbot/history/"),
};

export default chatbotApi;
