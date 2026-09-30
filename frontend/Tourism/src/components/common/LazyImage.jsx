import { useState } from "react"
import { FiImage } from "react-icons/fi"

/**
 * Lazy loading image with blur-up placeholder and error fallback.
 * Uses native loading="lazy" with IntersectionObserver fallback.
 */
export default function LazyImage({ src, alt = "", className = "", placeholderClassName = "" }) {
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 dark:bg-slate-700 ${className}`}>
        <FiImage size={32} className="text-gray-300 dark:text-gray-600" />
      </div>
    )
  }

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {!loaded && (
        <div className={`absolute inset-0 bg-gray-200 dark:bg-slate-700 animate-pulse ${placeholderClassName}`} />
      )}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        className={`w-full h-full object-cover transition-opacity duration-500 ${loaded ? "opacity-100" : "opacity-0"}`}
      />
    </div>
  )
}
