import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiMaximize2, FiChevronLeft, FiChevronRight, FiX } from "react-icons/fi"

export default function DestinationGallery({ images = [], name = "Destination" }) {
  const [activeIdx, setActiveIdx] = useState(0)
  const [lightboxOpen, setLightboxOpen] = useState(false)

  if (!images || images.length === 0) return null

  return (
    <div className="space-y-3">
      <div className="relative h-[380px] sm:h-[480px] rounded-3xl overflow-hidden shadow-2xl bg-black group">
        <img
          src={images[activeIdx] || images[0]}
          alt={name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 cursor-pointer"
          onClick={() => setLightboxOpen(true)}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none" />

        <div className="absolute top-4 right-4">
          <button
            onClick={() => setLightboxOpen(true)}
            className="p-2.5 rounded-xl bg-black/60 hover:bg-black/80 text-white backdrop-blur flex items-center gap-1.5 text-xs font-semibold"
          >
            <FiMaximize2 size={14} /> Fullscreen ({images.length} Photos)
          </button>
        </div>

        <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between text-white">
          <div>
            <span className="px-3 py-1 rounded-full bg-amber-400 text-gray-950 font-bold text-xs uppercase">
              {name}
            </span>
            <p className="text-xs text-white/80 mt-1">Photo {activeIdx + 1} of {images.length}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveIdx((p) => (p === 0 ? images.length - 1 : p - 1))}
              className="p-3 rounded-full bg-white/30 hover:bg-white text-gray-900 backdrop-blur transition-all"
            >
              <FiChevronLeft size={18} />
            </button>
            <button
              onClick={() => setActiveIdx((p) => (p === images.length - 1 ? 0 : p + 1))}
              className="p-3 rounded-full bg-white/30 hover:bg-white text-gray-900 backdrop-blur transition-all"
            >
              <FiChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2 no-scrollbar">
        {images.map((imgUrl, idx) => (
          <button
            key={idx}
            onClick={() => setActiveIdx(idx)}
            className={`relative w-24 sm:w-28 h-16 sm:h-20 rounded-xl overflow-hidden shrink-0 border-2 transition-all ${
              activeIdx === idx
                ? "border-amber-400 ring-2 ring-amber-400 scale-105"
                : "border-transparent opacity-60 hover:opacity-100"
            }`}
          >
            <img loading="lazy" decoding="async" src={imgUrl} alt={`Thumb ${idx + 1}`} className="w-full h-full object-cover" />
          </button>
        ))}
      </div>

<<<<<<< HEAD
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
                <span className="absolute top-2 left-2 px-2 py-0.5 text-xs font-bold rounded-full bg-black/50 text-white">
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
=======
      <AnimatePresence>
        {lightboxOpen && (
          <div className="fixed inset-0 z-50 bg-black/95 flex flex-col justify-between p-4 sm:p-6 backdrop-blur-md">
            <div className="flex items-center justify-between text-white border-b border-white/10 pb-3">
              <span className="font-bold text-base text-amber-300">
                {name} · Photo {activeIdx + 1} of {images.length}
              </span>
              <button
                onClick={() => setLightboxOpen(false)}
                className="p-2 rounded-full bg-white/20 hover:bg-white/40 text-white"
              >
                <FiX size={24} />
>>>>>>> origin/arena/01a0ed99-tourism
              </button>
            </div>

            <div className="flex-1 min-w-0 flex items-center justify-center relative my-4">
              <img
                src={images[activeIdx]}
                alt="Fullscreen"
                className="max-h-[78vh] max-w-full object-contain rounded-2xl shadow-2xl"
              />
              <button
                onClick={() => setActiveIdx((p) => (p === 0 ? images.length - 1 : p - 1))}
                className="absolute left-4 p-4 rounded-full bg-black/50 hover:bg-black/80 text-white backdrop-blur"
              >
                <FiChevronLeft size={28} />
              </button>
              <button
                onClick={() => setActiveIdx((p) => (p === images.length - 1 ? 0 : p + 1))}
                className="absolute right-4 p-4 rounded-full bg-black/50 hover:bg-black/80 text-white backdrop-blur"
              >
                <FiChevronRight size={28} />
              </button>
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
