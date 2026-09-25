import { useEffect, useState } from "react"
import { FiImage } from "react-icons/fi"
import { fallbackImageUrl } from "../../utils/imageUtils"

function getFallbackForTitle(title) {
  if (!title) return ""
  return fallbackImageUrl(title) || ""
}

const PlaceholderImage = ({ className = "", title = "Nepal Attraction", src = null, alt = "" }) => {
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setFailed(false), 0)
    return () => clearTimeout(timer)
  }, [src])

  const effectiveSrc = (!src || failed) ? getFallbackForTitle(title || alt) : src

  if (!effectiveSrc) {
    return (
      <div className={`flex items-center justify-center bg-[var(--ny-soft-green)] text-[var(--ny-green)] ${className}`} role="img" aria-label={alt || `${title || "Destination"} image unavailable`}>
        <span className="flex flex-col items-center gap-2 px-4 text-center"><FiImage size={26} aria-hidden="true" /><span className="text-xs font-semibold">Image unavailable</span></span>
      </div>
    )
  }

  return <img src={effectiveSrc} alt={alt || title || "Nepal Landmark"} loading="lazy" onError={() => setFailed(true)} className={`object-cover ${className}`} />
}

export default PlaceholderImage
