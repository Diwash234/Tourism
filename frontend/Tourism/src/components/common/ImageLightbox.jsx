import { useState, useEffect, useCallback } from "react"
import { FiX, FiChevronLeft, FiChevronRight, FiZoomIn, FiZoomOut, FiDownload, FiShare2 } from "react-icons/fi"

/**
 * Full-screen image lightbox with keyboard navigation,
 * zoom controls, and download/share actions.
 */
export default function ImageLightbox({ images = [], initialIndex = 0, onClose }) {
  const [current, setCurrent] = useState(initialIndex)
  const [zoom, setZoom] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  const goNext = useCallback(() => {
    setCurrent(i => (i + 1) % images.length)
    setZoom(1)
    setPosition({ x: 0, y: 0 })
  }, [images.length])

  const goPrev = useCallback(() => {
    setCurrent(i => (i - 1 + images.length) % images.length)
    setZoom(1)
    setPosition({ x: 0, y: 0 })
  }, [images.length])

  const handleKeyDown = useCallback((e) => {
    if (e.key === "Escape") onClose()
    if (e.key === "ArrowRight") goNext()
    if (e.key === "ArrowLeft") goPrev()
    if (e.key === "+" || e.key === "=") setZoom(z => Math.min(z + 0.25, 3))
    if (e.key === "-") setZoom(z => Math.max(z - 0.25, 0.5))
  }, [onClose, goNext, goPrev])

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    document.body.style.overflow = "hidden"
    return () => {
      window.removeEventListener("keydown", handleKeyDown)
      document.body.style.overflow = ""
    }
  }, [handleKeyDown])

  const handleMouseDown = (e) => {
    if (zoom > 1) {
      setDragging(true)
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
    }
  }

  const handleMouseMove = (e) => {
    if (dragging) {
      setPosition({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y })
    }
  }

  const handleMouseUp = () => setDragging(false)

  const handleDownload = async () => {
    const img = images[current]
    const url = typeof img === "string" ? img : img.src
    try {
      const res = await fetch(url)
      const blob = await res.blob()
      const link = document.createElement("a")
      link.href = URL.createObjectURL(blob)
      link.download = `image-${current + 1}.jpg`
      link.click()
      URL.revokeObjectURL(link.href)
    } catch {
      window.open(url, "_blank")
    }
  }

  const handleShare = async () => {
    const img = images[current]
    const url = typeof img === "string" ? img : img.src
    const title = typeof img === "string" ? "Image" : img.alt || "Image"
    if (navigator.share) {
      try { await navigator.share({ title, url }) } catch { /* cancelled */ }
    } else {
      await navigator.clipboard.writeText(url)
      alert("Link copied to clipboard!")
    }
  }

  const currentImage = images[current]
  const src = typeof currentImage === "string" ? currentImage : currentImage?.src
  const alt = typeof currentImage === "string" ? `Image ${current + 1}` : currentImage?.alt || `Image ${current + 1}`

  return (
    <div className="fixed inset-0 z-[100] bg-black/95 flex flex-col" role="dialog" aria-modal="true" aria-label="Image viewer">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-black/50">
        <span className="text-white text-sm font-semibold">
          {current + 1} / {images.length}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setZoom(z => Math.max(z - 0.25, 0.5))}
            className="p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Zoom out"
          >
            <FiZoomOut size={18} />
          </button>
          <span className="text-white/70 text-xs min-w-[40px] text-center">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            onClick={() => setZoom(z => Math.min(z + 0.25, 3))}
            className="p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Zoom in"
          >
            <FiZoomIn size={18} />
          </button>
          <div className="w-px h-6 bg-white/20 mx-1" />
          <button
            type="button"
            onClick={handleDownload}
            className="p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Download"
          >
            <FiDownload size={18} />
          </button>
          <button
            type="button"
            onClick={handleShare}
            className="p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Share"
          >
            <FiShare2 size={18} />
          </button>
          <div className="w-px h-6 bg-white/20 mx-1" />
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Close"
          >
            <FiX size={18} />
          </button>
        </div>
      </div>

      {/* Image Area */}
      <div
        className="flex-1 flex items-center justify-center overflow-hidden relative"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <img
          src={src}
          alt={alt}
          className="max-w-full max-h-full object-contain transition-transform duration-200"
          style={{ transform: `scale(${zoom}) translate(${position.x / zoom}px, ${position.y / zoom}px)` }}
          draggable={false}
        />

        {/* Navigation Arrows */}
        {images.length > 1 && (
          <>
            <button
              type="button"
              onClick={goPrev}
              className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/50 text-white/70 hover:text-white hover:bg-black/70 transition-colors"
              aria-label="Previous image"
            >
              <FiChevronLeft size={24} />
            </button>
            <button
              type="button"
              onClick={goNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/50 text-white/70 hover:text-white hover:bg-black/70 transition-colors"
              aria-label="Next image"
            >
              <FiChevronRight size={24} />
            </button>
          </>
        )}
      </div>

      {/* Thumbnail Strip */}
      {images.length > 1 && (
        <div className="flex items-center justify-center gap-2 px-4 py-3 bg-black/50 overflow-x-auto">
          {images.map((img, i) => {
            const thumbSrc = typeof img === "string" ? img : img.src
            return (
              <button
                key={i}
                type="button"
                onClick={() => { setCurrent(i); setZoom(1); setPosition({ x: 0, y: 0 }) }}
                className={`shrink-0 w-14 h-14 rounded-lg overflow-hidden border-2 transition-all ${
                  i === current ? "border-white scale-105" : "border-transparent opacity-50 hover:opacity-75"
                }`}
              >
                <img src={thumbSrc} alt="" className="w-full h-full object-cover" />
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
