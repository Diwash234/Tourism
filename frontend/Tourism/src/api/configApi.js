import axiosClient from "./axiosClient"

const configApi = {
  // The _ts cache-buster makes every URL unique, so no Cache-Control request
  // header is needed — keeping the request "simple" avoids a CORS preflight
  // round-trip on every config load (CMS brief §2: remove unnecessary custom
  // headers rather than widening the backend's allowed-header list).
  getPublicConfig: (lang) => axiosClient.get("/config/public/", { params: { ...(lang ? { lang } : {}), _ts: Date.now() } }),
  // Footer newsletter (CMS brief §6) — public, stores real signups server-side.
  subscribeNewsletter: (email) => axiosClient.post("/newsletter/subscribe/", { email }),
}

export default configApi
