import React, { useState } from "react"
import { FiImage } from "react-icons/fi"

const AUTHENTIC_FALLBACK_IMAGES = [
  "/images/destinations/pokhara/img1.jpg",
  "/images/destinations/annapurna/img1.jpg",
  "/images/destinations/everest/img1.jpg",
  "/images/destinations/mustang/img1.jpg",
  "/images/destinations/rara/img1.jpg",
  "/images/destinations/chitwan/img1.jpg",
  "/images/destinations/bhaktapur/img1.jpg",
  "/images/destinations/lumbini/img1.jpg",
  "/images/destinations/ilam/img1.jpg",
  "/images/destinations/nagarkot/img1.jpg",
  "/images/destinations/tilicho/img1.jpg",
  "/images/destinations/bandipur/img1.jpg",
]

/**
 * PlaceholderImage
 * Renders an authentic Nepal landscape photograph rather than a blank solid colored box.
 * Cycles through verified regional photography based on the item seed.
 */
const PlaceholderImage = ({ seed = 0, className = "", title = "Nepal Landmark", category = "" }) => {
  const [loadError, setLoadError] = useState(false)
  const idx = Math.abs(Number(seed) || 0) % AUTHENTIC_FALLBACK_IMAGES.length
  const photoUrl = AUTHENTIC_FALLBACK_IMAGES[idx] || AUTHENTIC_FALLBACK_IMAGES[0]

  if (loadError) {
    return (
      <div className={`relative flex items-center justify-center bg-slate-900 text-white/60 overflow-hidden ${className}`}>
        <img
          src="https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80"
          alt={title}
          className="w-full h-full object-cover opacity-80"
        />
        <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
          <FiImage size={24} className="text-amber-300/80" />
        </div>
      </div>
    )
  }

  return (
    <div className={`relative overflow-hidden bg-slate-900 ${className}`}>
      <img
        src={photoUrl}
        alt={title}
        loading="lazy"
        onError={() => setLoadError(true)}
        className="w-full h-full object-cover"
      />
    </div>
  )
}

export default PlaceholderImage
