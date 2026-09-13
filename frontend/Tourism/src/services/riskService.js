// "Risk" maps to the existing alerts + ML safety endpoints — there's no
// separate risk API, alertApi already covers /alerts/ and the ML safety
// score. Re-exported under this name to match the requested service
// layer naming.
export { default } from "../api/alertApi"