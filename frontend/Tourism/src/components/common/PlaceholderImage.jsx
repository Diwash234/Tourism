import { useEffect, useState } from "react"
import { FiImage } from "react-icons/fi"

/** Explicit missing-media state. Never substitutes another place's photo. */
const PlaceholderImage = ({ className = "", title = "Image unavailable", src = null, alt = "" }) => {
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [src])
  if (src && !failed) {
    return <img src={src} alt={alt || title} loading="lazy" onError={() => setFailed(true)} className={`object-cover ${className}`} />
  }
  return <div role="img" aria-label={`${title}: image unavailable`} className={`flex flex-col items-center justify-center gap-2 bg-slate-100 text-slate-400 ${className}`}>
    <FiImage size={28} />
    <span className="text-xs font-bold">Image unavailable</span>
    <span className="text-[10px] text-center px-3">No verified media for {title}</span>
  </div>
}

export default PlaceholderImage
