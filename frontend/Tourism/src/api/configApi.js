import axiosClient from "./axiosClient"

const configApi = {
  getPublicConfig: () => axiosClient.get("/config/public/"),
}

export default configApi
