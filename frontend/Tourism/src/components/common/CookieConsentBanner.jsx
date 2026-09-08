import { useState } from "react"
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

  if (!consent.enabled || hidden) return null

  const accept = () => {
    dismissCookieConsent(window.localStorage)
    setHidden(true)
  }

  return (
    <div
      role="region"
      aria-label="Cookie consent"
      className="fixed bottom-3 left-3 right-3 sm:left-auto sm:right-5 sm:max-w-md z-[70] rounded-2xl border border-emerald-500/40 bg-slate-900/95 backdrop-blur p-4 shadow-2xl"
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
            className="inline-flex items-center gap-1 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-black text-slate-950 hover:bg-emerald-400"
          >
            <FiCheck size={13} /> Accept
          </button>
          <button
            type="button"
            onClick={accept}
            aria-label="Dismiss cookie notice"
            className="rounded-lg border border-emerald-500/40 p-1.5 text-emerald-200 hover:bg-emerald-500/20"
          >
            <FiX size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
