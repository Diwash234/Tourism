/**
 * Cookie consent (CMS brief §17).
 *
 * Stored as the public `cookie_consent` SiteSetting row ({enabled, message})
 * and served through the public config, so admins control the banner with no
 * rebuild. The site genuinely uses essential cookies/localStorage (auth
 * token, language preference, theme), so the default message is truthful.
 * Acceptance persists per browser; storage is injected so the helpers stay
 * testable and survive private-mode failures.
 */

export const COOKIE_CONSENT_KEY = "tourism_cookie_consent"

export const DEFAULT_COOKIE_MESSAGE =
  "We use essential cookies to keep you signed in and remember your language and theme. See our Privacy Policy for details."

export const resolveCookieConsent = (value) => {
  const source = value && typeof value === "object" ? value : {}
  return {
    enabled: source.enabled !== false,
    message:
      typeof source.message === "string" && source.message.trim()
        ? source.message.trim()
        : DEFAULT_COOKIE_MESSAGE,
  }
}

export const isCookieConsentDismissed = (storage) => {
  try {
    return storage?.getItem(COOKIE_CONSENT_KEY) === "accepted"
  } catch {
    return false
  }
}

export const dismissCookieConsent = (storage) => {
  try {
    storage?.setItem(COOKIE_CONSENT_KEY, "accepted")
  } catch {
    /* private-mode storage — banner simply returns next visit */
  }
}
