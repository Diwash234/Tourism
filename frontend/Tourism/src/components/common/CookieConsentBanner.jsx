import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import usePublicConfig from "../../hooks/usePublicConfig"
import useCookieChoice from "../../hooks/useCookieChoice"
import { OPEN_SETTINGS_EVENT, resolveCookieConsent, saveCookieChoice } from "../../utils/cookieConsent"

/**
 * Cookie notice with one real choice: whether embedded YouTube/Vimeo players
 * may load. Both answers are equally prominent, nothing loads before a choice,
 * and "Cookie settings" in the footer reopens it. Text and on/off come from the
 * public `cookie_consent` setting (admin panel, no rebuild).
 */
export default function CookieConsentBanner() {
  const { settings } = usePublicConfig()
  const consent = resolveCookieConsent(settings?.cookie_consent)
  const choice = useCookieChoice()
  const [reopened, setReopened] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const bannerRef = useRef(null)
  const firstButtonRef = useRef(null)

  useEffect(() => {
    const onChatToggle = (event) => setChatOpen(Boolean(event.detail?.open))
    const onOpen = () => setReopened(true)
    window.addEventListener("ny-chat-toggle", onChatToggle)
    window.addEventListener(OPEN_SETTINGS_EVENT, onOpen)
    return () => {
      window.removeEventListener("ny-chat-toggle", onChatToggle)
      window.removeEventListener(OPEN_SETTINGS_EVENT, onOpen)
    }
  }, [])

  // Settings reopened from the footer always show, even if chat is open.
  const visibleNow = reopened || (consent.enabled && choice === null && !chatOpen)

  useEffect(() => {
    document.body.classList.toggle("ny-cookie-visible", visibleNow)
    return () => document.body.classList.remove("ny-cookie-visible")
  }, [visibleNow])

  useEffect(() => {
    if (reopened) firstButtonRef.current?.focus()
  }, [reopened])

  // Publish the banner's real height so the footer can reserve exactly that
  // much room (the end of the page must never be stuck under the banner).
  useEffect(() => {
    const el = bannerRef.current
    const root = document.documentElement
    if (!visibleNow || !el) { root.style.removeProperty("--ny-cookie-h"); return undefined }
    const publish = () => root.style.setProperty("--ny-cookie-h", `${Math.ceil(el.getBoundingClientRect().height)}px`)
    publish()
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(publish) : null
    ro?.observe(el)
    return () => { ro?.disconnect(); root.style.removeProperty("--ny-cookie-h") }
  }, [visibleNow])

  if (!visibleNow) return null

  const choose = (media) => {
    saveCookieChoice(window.localStorage, { media })
    setReopened(false)
  }

  const current = choice === null ? null : choice.media ? "Videos are currently allowed." : "Videos are currently blocked."

  return (
    <div
      ref={bannerRef}
      role="region"
      aria-labelledby="ny-cookie-title"
      className="ny-cookie-banner fixed left-3 right-3 max-h-[40vh] overflow-y-auto rounded-[var(--ny-radius-lg)] border border-white/15 bg-[var(--ny-green-deepest)] p-4 text-white shadow-[var(--ny-shadow-elevated)] lg:left-5 lg:right-auto lg:max-w-md"
    >
      <h2 id="ny-cookie-title" className="text-sm font-bold">Cookies and embedded videos</h2>
      <p className="mt-1 text-xs leading-relaxed text-emerald-50">
        {consent.message}{" "}
        <Link to="/cookie-policy" className="font-bold text-white underline underline-offset-2">Cookie Policy</Link>
      </p>
      {current && <p className="mt-1 text-xs text-emerald-100" aria-live="polite">{current}</p>}
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button ref={firstButtonRef} type="button" onClick={() => choose(false)} className="ny-cookie-choice">
          Essential only
        </button>
        <button type="button" onClick={() => choose(true)} className="ny-cookie-choice">
          Allow videos
        </button>
      </div>
    </div>
  )
}
