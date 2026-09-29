/**
 * Cookie and embedded-media consent.
 *
 * What the site stores (see /cookie-policy): only storage needed to run it
 * (sign-in tokens, language, theme, offline data). There are no analytics or
 * advertising cookies, so the only real choice is whether to load embedded
 * YouTube or Vimeo players, which can set their own cookies. Until the visitor
 * allows that, CMS video blocks show a click-to-load placeholder and no request
 * reaches those services.
 *
 * The banner text and on/off switch come from the public `cookie_consent`
 * SiteSetting. Storage is injected so the helpers stay testable and survive
 * private-mode failures.
 */

export const COOKIE_CONSENT_KEY = "tourism_cookie_consent"
export const CONSENT_EVENT = "ny-consent-change"
export const OPEN_SETTINGS_EVENT = "ny-open-cookie-settings"

export const DEFAULT_COOKIE_MESSAGE =
  "Nepal Yatra only stores what it needs to work: your sign-in, language, theme and offline data. There are no analytics or advertising cookies. Videos from YouTube or Vimeo load only if you allow them."

// Earlier default wording; replaced so the banner matches the real choice.
const LEGACY_DEFAULT_MESSAGE =
  "We use essential cookies to keep you signed in and remember your language and theme. See our Privacy Policy for details."

export const resolveCookieConsent = (value) => {
  const source = value && typeof value === "object" ? value : {}
  const message = typeof source.message === "string" ? source.message.trim() : ""
  return {
    enabled: source.enabled !== false,
    message: message && message !== LEGACY_DEFAULT_MESSAGE ? message : DEFAULT_COOKIE_MESSAGE,
  }
}

/** The visitor's saved choice, or null if they have not chosen yet. */
export const readCookieChoice = (storage) => {
  try {
    const raw = storage?.getItem(COOKIE_CONSENT_KEY)
    if (!raw || raw === "accepted") return null // old notice-only value: ask again
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === "object" ? { media: parsed.media === true } : null
  } catch {
    return null
  }
}

export const isCookieConsentDismissed = (storage) => readCookieChoice(storage) !== null

export const saveCookieChoice = (storage, { media }) => {
  const choice = { media: media === true }
  try {
    storage?.setItem(COOKIE_CONSENT_KEY, JSON.stringify({ ...choice, at: new Date().toISOString() }))
  } catch {
    /* private-mode storage: the choice lasts for this page view only */
  }
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent(CONSENT_EVENT, { detail: choice }))
  return choice
}

export const openCookieSettings = () => {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(OPEN_SETTINGS_EVENT))
}

/** youtube.com and youtu.be links become privacy-enhanced embeds; Vimeo gets dnt=1. */
export const privacyEmbedUrl = (url = "") => {
  const yt = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{6,})/)
  if (yt) return `https://www.youtube-nocookie.com/embed/${yt[1]}`
  const vimeo = url.match(/vimeo\.com\/(?:video\/)?(\d+)/)
  if (vimeo) return `https://player.vimeo.com/video/${vimeo[1]}?dnt=1`
  return ""
}
