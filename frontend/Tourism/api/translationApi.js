import axiosClient from "./axiosClient"

const translationApi = {
  translateText: (payload) => axiosClient.post("/translation/translate", payload),
  getSupportedLanguages: () => axiosClient.get("/translation/languages"),
}

export default translationApi