import axios from "axios"
import axiosClient from "../src/api/axiosClient"
import { setLang } from "../src/i18n"
import { resetForTests } from "../src/i18n/dynamicTranslate"

export const requests = []
let failing = false
export const setFailing = (v) => { failing = v }
const adapter = async (config) => {
  const body = typeof config.data === "string" ? JSON.parse(config.data) : config.data
  requests.push(body)
  if (failing) { const e = new Error("down"); e.response = { status: 503, data: {}, config }; e.config = config; throw e }
  return { data: { translations: body.texts.map((t) => `NE[${t}]`) }, status: 200, statusText: "OK", headers: {}, config, request: {} }
}
axiosClient.defaults.adapter = adapter
axios.defaults.adapter = adapter
export { setLang, resetForTests }
