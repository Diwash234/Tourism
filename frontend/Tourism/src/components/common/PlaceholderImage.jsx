import React, { useState, useMemo } from "react"

/**
 * PlaceholderImage
 *
 * Renders a REAL Nepal landscape photograph (openly licensed, Unsplash
 * License) as a fallback. The previous version pointed at bundled
 * /images/destinations/* JPEGs that were actually flat purple colour
 * blocks with a text label -- those have been removed from the fallback
 * list. The picked image is deterministic per `seed` so the same card
 * always shows the same photo, while different cards vary.
 */
const FALLBACK_IMAGES = [
  "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&q=80",
  "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&q=80",
  "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80",
  "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&q=80",
  "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&q=80",
  "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1200&q=80",
  "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80",
  "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80",
  "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80",
  "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80",
  "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1200&q=80",
  "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1200&q=80",
]

// Reuse the curated place-specific photo map from imageUtils so specific
// named destinations always show their matching real photo.
import { LOCAL_NEPAL_PHOTOS_PLACEHOLDER } from "../../utils/imageUtils"

const matchLocal = (name) => {
  if (!name) return null
  const n = String(name).toLowerCase().trim()
  // Imported map (mirror of LOCAL_NEPAL_PHOTOS) is defined below.
  if (LOCAL_NEPAL_PHOTOS_PLACEHOLDER[n]) return LOCAL_NEPAL_PHOTOS_PLACEHOLDER[n]
  for (const key of Object.keys(LOCAL_NEPAL_PHOTOS_PLACEHOLDER)) {
    if (n.includes(key)) return LOCAL_NEPAL_PHOTOS_PLACEHOLDER[key]
  }
  return null
}

const PlaceholderImage = ({ seed = 0, className = "", title = "Nepal landscape", src = null, alt = "" }) => {
  const [error, setError] = useState(false)

  const photoUrl = useMemo(() => {
    if (src && !error) return src
    // 1. Try place-specific local photo if the title names a known place
    const local = matchLocal(title)
    if (local) return local
    // 2. Otherwise deterministic varied Unsplash pool
    let h = 0
    const s = String(seed ?? title ?? "nepal")
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
    return FALLBACK_IMAGES[h % FALLBACK_IMAGES.length]
  }, [src, seed, title, error])

  return (
    <div className={`relative overflow-hidden bg-slate-900 ${className}`}>
      <img
        src={photoUrl}
        alt={alt || title}
        loading="lazy"
        onError={() => setError(true)}
        className="w-full h-full object-cover"
      />
    </div>
  )
}

export default PlaceholderImage
