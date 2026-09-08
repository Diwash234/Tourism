import axiosClient from "./axiosClient"

const configApi = {
  getPublicConfig: (lang) => axiosClient.get("/config/public/", { params: { ...(lang ? { lang } : {}), _ts: Date.now() }, headers: { "Cache-Control": "no-cache" } }),
  // Footer newsletter (CMS brief §6) — public, stores real signups server-side.
  subscribeNewsletter: (email) => axiosClient.post("/newsletter/subscribe/", { email }),
}

export default configApi
