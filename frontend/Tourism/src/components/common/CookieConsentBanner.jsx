import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiCheck, FiX } from "react-icons/fi"
import usePublicConfig from "../../hooks/usePublicConfig"
import { resolveCookieConsent, isCookieConsentDismissed, dismissCookieConsent } from "../../utils/cookieConsent"

/**
 * Cookie consent banner (CMS brief §17).
 *
 * Enabled state and message come from the public `cookie_consent` setting,
 * so admins control it from the admin panel with no rebuild. Accepting (or
 * dismissing) persists in the visitor's browser; the banner defaults to
 * shown until the setting explicitly disables it or the visitor accepts.
 */
export default function CookieConsentBanner() {
  const { settings } = usePublicConfig()
  const consent = resolveCookieConsent(settings?.cookie_consent)
  const [hidden, setHidden] = useState(() => isCookieConsentDismissed(window.localStorage))
  const [chatOpen, setChatOpen] = useState(false)

  useEffect(() => {
    const onChatToggle = (event) => setChatOpen(Boolean(event.detail?.open))
    window.addEventListener("ny-chat-toggle", onChatToggle)
    return () => window.removeEventListener("ny-chat-toggle", onChatToggle)
  }, [])

  useEffect(() => {
    const visible = consent.enabled && !hidden && !chatOpen
    document.body.classList.toggle("ny-cookie-visible", visible)
    return () => document.body.classList.remove("ny-cookie-visible")
  }, [consent.enabled, hidden, chatOpen])

  if (!consent.enabled || hidden || chatOpen) return null

  const accept = () => {
    dismissCookieConsent(window.localStorage)
    setHidden(true)
  }

  return (
    <div
      role="region"
      aria-live="polite"
      aria-label="Cookie consent"
      className="ny-cookie-banner fixed left-3 right-3 max-h-[34vh] overflow-y-auto rounded-[var(--ny-radius-lg)] border border-white/15 bg-[var(--ny-green-deepest)] p-4 text-white shadow-[var(--ny-shadow-elevated)] backdrop-blur lg:left-5 lg:right-auto lg:max-w-md"
    >
      <div className="flex items-start gap-3">
        <p className="text-xs leading-relaxed text-emerald-100 flex-1">
          {consent.message}{" "}
          <Link to="/privacy" className="font-bold text-emerald-300 underline hover:text-white">
            Privacy Policy
          </Link>
        </p>
        <div className="flex shrink-0 items-center gap-1.5">
          <button
            type="button"
            onClick={accept}
            className="ny-btn ny-btn-accent min-h-11 px-3 text-xs"
          >
            <FiCheck size={13} /> Accept
          </button>
          <button
            type="button"
            onClick={accept}
            aria-label="Dismiss cookie notice"
            className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-sm)] border border-white/25 text-white hover:bg-white/10"
          >
            <FiX size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
