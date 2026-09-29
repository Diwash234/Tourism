import { useEffect, useState } from "react"
import { FiImage } from "react-icons/fi"
import { fallbackImageUrl } from "../../utils/imageUtils"

function getFallbackForTitle(title) {
  if (!title) return ""
  return fallbackImageUrl(title) || ""
}

// labelPlacement="top": for full-bleed background images with text laid over
// the bottom (hero / editorial tiles) -- keeps the honest "Image unavailable"
// tag out of the way of the overlaid title instead of centring it beneath.
const PlaceholderImage = ({ className = "", title = "Nepal Attraction", src = null, alt = "", labelPlacement = "center" }) => {
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setFailed(false), 0)
    return () => clearTimeout(timer)
  }, [src])

  const effectiveSrc = (!src || failed) ? getFallbackForTitle(title || alt) : src

  if (!effectiveSrc) {
    if (labelPlacement === "top") {
      return (
        <div className={`flex items-start justify-end bg-[var(--ny-green-dark)] p-3 ${className}`} role="img" aria-label={alt || `${title || "Destination"} image unavailable`}>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-black/35 px-2.5 py-1 text-xs font-semibold text-white/85"><FiImage size={13} aria-hidden="true" />Image unavailable</span>
        </div>
      )
    }
    return (
      <div className={`flex items-center justify-center bg-[var(--ny-soft-green)] text-[var(--ny-green)] ${className}`} role="img" aria-label={alt || `${title || "Destination"} image unavailable`}>
        <span className="flex flex-col items-center gap-2 px-4 text-center"><FiImage size={26} aria-hidden="true" /><span className="text-xs font-semibold">Image unavailable</span></span>
      </div>
    )
  }

  return <img src={effectiveSrc} alt={alt || title || "Nepal Landmark"} loading="lazy" onError={() => setFailed(true)} className={`object-cover ${className}`} />
}

export default PlaceholderImage
