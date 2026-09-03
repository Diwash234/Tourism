import axiosClient from "./axiosClient"

const configApi = {
  getPublicConfig: (lang) => axiosClient.get("/config/public/", { params: lang ? { lang } : {} }),
}

export default configApi
