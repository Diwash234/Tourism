import { useSyncExternalStore } from "react"
import { CONSENT_EVENT, COOKIE_CONSENT_KEY, readCookieChoice } from "../utils/cookieConsent"

const storage = () => (typeof window === "undefined" ? null : window.localStorage)

const subscribe = (onChange) => {
  const onStorage = (event) => { if (event.key === COOKIE_CONSENT_KEY) onChange() }
  window.addEventListener(CONSENT_EVENT, onChange)
  window.addEventListener("storage", onStorage)
  return () => {
    window.removeEventListener(CONSENT_EVENT, onChange)
    window.removeEventListener("storage", onStorage)
  }
}

// Serialise so useSyncExternalStore sees a stable snapshot between changes.
const snapshot = () => JSON.stringify(readCookieChoice(storage()))

/** Current consent choice ({ media } or null when undecided); live-updates. */
export default function useCookieChoice() {
  return JSON.parse(useSyncExternalStore(subscribe, snapshot, () => "null"))
}
