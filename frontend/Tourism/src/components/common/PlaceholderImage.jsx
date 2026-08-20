import { useEffect, useState } from "react"
import { FiImage } from "react-icons/fi"

/** Explicit missing-media state. Never substitutes another place's photo. */
const PlaceholderImage = ({ className = "", title = "Image unavailable", src = null, alt = "", cropBox = null }) => {
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [src])
  if (src && !failed) {
    const x = Number(cropBox?.x) || 0
    const y = Number(cropBox?.y) || 0
    const w = Number(cropBox?.w) || 100
    const h = Number(cropBox?.h) || 100
    const cropped = cropBox && (x || y || w !== 100 || h !== 100)
    return (
      <img
        src={src}
        alt={alt || title}
        loading="lazy"
        onError={() => setFailed(true)}
        className={`object-cover ${className}`}
        style={cropped ? { clipPath: `inset(${y}% ${Math.max(0, 100 - x - w)}% ${Math.max(0, 100 - y - h)}% ${x}%)` } : undefined}
      />
    )
  }
  return <div role="img" aria-label={`${title}: image unavailable`} className={`flex flex-col items-center justify-center gap-2 bg-slate-100 text-slate-400 ${className}`}>
    <FiImage size={28} />
    <span className="text-xs font-bold">Image unavailable</span>
    <span className="text-[10px] text-center px-3">No verified media for {title}</span>
  </div>
}

export default PlaceholderImage
