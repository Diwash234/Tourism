import { useState } from "react"
import { FiX, FiChevronLeft, FiChevronRight, FiZoomIn } from "react-icons/fi"
import LazyImage from "./LazyImage"

/**
 * Image gallery with lightbox, keyboard navigation, and zoom support.
 */
export default function ImageGallery({ images = [], className = "" }) {
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)

  const openLightbox = (index) => {
    setCurrentIndex(index)
    setLightboxOpen(true)
  }

  const closeLightbox = () => setLightboxOpen(false)

  const goNext = () => setCurrentIndex(i => (i + 1) % images.length)
  const goPrev = () => setCurrentIndex(i => (i - 1 + images.length) % images.length)

  if (images.length === 0) return null

  return (
    <>
      <div className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 ${className}`}>
        {images.map((img, i) => (
          <button
            key={i}
            type="button"
            onClick={() => openLightbox(i)}
            className="relative group aspect-square rounded-xl overflow-hidden bg-gray-100 dark:bg-slate-700"
          >
            <LazyImage
              src={img.src || img}
              alt={img.alt || `Image ${i + 1}`}
              className="w-full h-full"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
              <FiZoomIn className="text-white opacity-0 group-hover:opacity-100 transition-opacity" size={24} />
            </div>
          </button>
        ))}
      </div>

      {lightboxOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center" role="dialog" aria-modal="true" aria-label="Image viewer">
          <div className="absolute inset-0 bg-black/90" onClick={closeLightbox} />
          <div className="relative z-10 max-w-4xl max-h-[90vh] w-full mx-4">
            <LazyImage
              src={images[currentIndex]?.src || images[currentIndex]}
              alt={images[currentIndex]?.alt || `Image ${currentIndex + 1}`}
              className="w-full max-h-[80vh] object-contain rounded-lg"
            />
            <button
              type="button"
              onClick={closeLightbox}
              className="absolute top-3 right-3 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
              aria-label="Close"
            >
              <FiX size={20} />
            </button>
            {images.length > 1 && (
              <>
                <button
                  type="button"
                  onClick={goPrev}
                  className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
                  aria-label="Previous image"
                >
                  <FiChevronLeft size={24} />
                </button>
                <button
                  type="button"
                  onClick={goNext}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
                  aria-label="Next image"
                >
                  <FiChevronRight size={24} />
                </button>
                <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                  {images.map((_, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setCurrentIndex(i)}
                      className={`h-2 rounded-full transition-all ${
                        i === currentIndex ? "w-6 bg-white" : "w-2 bg-white/40 hover:bg-white/60"
                      }`}
                      aria-label={`Go to image ${i + 1}`}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}
