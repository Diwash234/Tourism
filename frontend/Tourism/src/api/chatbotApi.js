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

  // ---- Human support workflow (admin dashboard) ----
  supportInbox: (params) => axiosClient.get("/chatbot/support/inbox/", { params }),
  supportThread: (conversationId) =>
    axiosClient.get(`/chatbot/support/thread/${conversationId}/`),
  supportReply: (conversationId, content) =>
    axiosClient.post("/chatbot/support/reply/", { conversation_id: conversationId, content }),
  supportAssign: (payload) =>
    axiosClient.post("/chatbot/support/assign/", payload),

}


export default chatbotApi
