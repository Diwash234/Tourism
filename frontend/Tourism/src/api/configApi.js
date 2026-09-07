import axiosClient from "./axiosClient"

const configApi = {
  getPublicConfig: (lang) => axiosClient.get("/config/public/", { params: { ...(lang ? { lang } : {}), _ts: Date.now() }, headers: { "Cache-Control": "no-cache" } }),
}

export default configApi
