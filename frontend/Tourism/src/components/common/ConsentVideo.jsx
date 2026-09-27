import { useState } from "react"
import { Link } from "react-router-dom"
import { FiPlay } from "react-icons/fi"
import useCookieChoice from "../../hooks/useCookieChoice"
import { privacyEmbedUrl, saveCookieChoice } from "../../utils/cookieConsent"

/**
 * YouTube/Vimeo embed that makes no request to the video host until the
 * visitor allows embedded videos (cookie banner) or plays this one video.
 */
export default function ConsentVideo({ url, title, className = "" }) {
  const choice = useCookieChoice()
  const [playOnce, setPlayOnce] = useState(false)
  const src = privacyEmbedUrl(url)
  if (!src) return null
  const host = src.includes("vimeo") ? "Vimeo" : "YouTube"
  const label = title || "Video"

  if (choice?.media || playOnce) {
    return (
      <iframe
        title={label}
        src={playOnce ? `${src}${src.includes("?") ? "&" : "?"}autoplay=1` : src}
        className={`aspect-video w-full border-0 ${className}`}
        allow="accelerometer; autoplay; encrypted-media; picture-in-picture"
        allowFullScreen
        loading="lazy"
      />
    )
  }

  return (
    <div className={`grid aspect-video w-full place-items-center bg-slate-900 p-4 text-center text-white ${className}`}>
      <div className="max-w-sm">
        <p className="text-sm font-bold">{label}</p>
        <p className="mt-1 text-xs leading-relaxed text-slate-300">
          This video is hosted on {host}, which may set its own cookies once it loads.{" "}
          <Link to="/cookie-policy" className="underline underline-offset-2">Cookie Policy</Link>
        </p>
        <div className="mt-3 flex flex-wrap justify-center gap-2">
          <button type="button" onClick={() => setPlayOnce(true)} className="ny-cookie-choice inline-flex items-center gap-1.5">
            <FiPlay aria-hidden="true" /> Play this video
          </button>
          <button type="button" onClick={() => saveCookieChoice(window.localStorage, { media: true })} className="ny-cookie-choice">
            Allow all videos
          </button>
        </div>
      </div>
    </div>
  )
}
