import { useState, useEffect, useCallback } from "react"
import { FiX, FiChevronLeft, FiChevronRight, FiZoomIn, FiDownload, FiShare2 } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import LazyImage from "../common/LazyImage"

/**
 * Photo gallery with masonry grid, lightbox, keyboard navigation,
 * and download/share actions.
 */
export default function DestinationGallery({ images = [], destinationName = "" }) {
  const { t: _t } = useTranslation()
  const [lightboxIndex, setLightboxIndex] = useState(null)
  const [filter, setFilter] = useState("all")

  const categories = ["all", "nature", "culture", "architecture", "people", "food"]
  const filtered = filter === "all" ? images : images.filter(img => img.category === filter)

  const openLightbox = useCallback((index) => setLightboxIndex(index), [])
  const closeLightbox = useCallback(() => setLightboxIndex(null), [])
  const goNext = useCallback(() => {
    setLightboxIndex(i => (i + 1) % filtered.length)
  }, [filtered.length])
  const goPrev = useCallback(() => {
    setLightboxIndex(i => (i - 1 + filtered.length) % filtered.length)
  }, [filtered.length])

  const handleKeyDown = useCallback((e) => {
    if (lightboxIndex === null) return
    if (e.key === "Escape") closeLightbox()
    if (e.key === "ArrowRight") goNext()
    if (e.key === "ArrowLeft") goPrev()
  }, [lightboxIndex, closeLightbox, goNext, goPrev])

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  const handleDownload = async (image) => {
    try {
      const res = await fetch(image.src || image)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${destinationName}-${Date.now()}.jpg`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      window.open(image.src || image, "_blank")
    }
  }

  const handleShare = async (image) => {
    const shareData = {
      title: destinationName,
      text: `Check out ${destinationName}`,
      url: image.src || image,
    }
    if (navigator.share) {
      try { await navigator.share(shareData) } catch { /* cancelled */ }
    } else {
      await navigator.clipboard.writeText(image.src || image)
      alert("Link copied to clipboard!")
    }
  }

  if (images.length === 0) return null

  return (
    <div className="space-y-4">
      {/* Category Filter */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {categories.map(cat => (
          <button
            key={cat}
            type="button"
            onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap transition-colors ${
              filter === cat
                ? "bg-[var(--ny-green)] text-white"
                : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
            }`}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      {/* Masonry Grid */}
      <div className="columns-2 sm:columns-3 lg:columns-4 gap-3 space-y-3">
        {filtered.map((image, i) => {
          const src = image.src || image
          const alt = image.alt || `${destinationName} photo ${i + 1}`
          return (
            <button
              key={i}
              type="button"
              onClick={() => openLightbox(i)}
              className="relative group block w-full rounded-xl overflow-hidden bg-gray-100 dark:bg-slate-700 break-inside-avoid"
            >
              <LazyImage src={src} alt={alt} className="w-full" />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                <FiZoomIn className="text-white opacity-0 group-hover:opacity-100 transition-opacity" size={24} />
              </div>
              {image.category && (
                <span className="absolute top-2 left-2 px-2 py-0.5 text-[10px] font-bold rounded-full bg-black/50 text-white">
                  {image.category}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Lightbox */}
      {lightboxIndex !== null && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center" role="dialog" aria-modal="true" aria-label="Image viewer">
          <div className="absolute inset-0 bg-black/95" onClick={closeLightbox} />
          <div className="relative z-10 max-w-5xl max-h-[90vh] w-full mx-4">
            <LazyImage
              src={filtered[lightboxIndex]?.src || filtered[lightboxIndex]}
              alt={filtered[lightboxIndex]?.alt || `${destinationName} photo ${lightboxIndex + 1}`}
              className="w-full max-h-[80vh] object-contain rounded-lg"
            />
            {/* Controls */}
            <div className="absolute top-3 right-3 flex gap-2">
              <button type="button" onClick={() => handleDownload(filtered[lightboxIndex])} className="p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors" aria-label="Download">
                <FiDownload size={18} />
              </button>
              <button type="button" onClick={() => handleShare(filtered[lightboxIndex])} className="p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors" aria-label="Share">
                <FiShare2 size={18} />
              </button>
              <button type="button" onClick={closeLightbox} className="p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors" aria-label="Close">
                <FiX size={18} />
              </button>
            </div>
            {/* Navigation */}
            {filtered.length > 1 && (
              <>
                <button type="button" onClick={goPrev} className="absolute left-3 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors" aria-label="Previous">
                  <FiChevronLeft size={24} />
                </button>
                <button type="button" onClick={goNext} className="absolute right-3 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors" aria-label="Next">
                  <FiChevronRight size={24} />
                </button>
              </>
            )}
            {/* Counter */}
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-black/50 text-white text-xs font-semibold">
              {lightboxIndex + 1} / {filtered.length}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
