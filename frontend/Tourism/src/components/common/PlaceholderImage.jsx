import React, { useState, useMemo } from "react"

/**
 * PlaceholderImage
 *
 * Renders a REAL Nepal photo as a fallback — first the curated local
 * landmark photo for the named place (40 unique /images/destinations/*
 * photos, no external hotlinks), otherwise a deterministic pick from that
 * same pool keyed by `seed`, so different cards always show different
 * photos and no card repeats the same image as its neighbour.
 */
import { LOCAL_NEPAL_PHOTOS_PLACEHOLDER } from "../../utils/imageUtils"

// Pool of unique local landmark photos (no Unsplash, no repeats).
const FALLBACK_IMAGES = [...new Set(Object.values(LOCAL_NEPAL_PHOTOS_PLACEHOLDER))]

const matchLocal = (name) => {
  if (!name) return null
  const n = String(name).toLowerCase().trim()
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
    // 2. Otherwise deterministic varied local-landmark pool
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
