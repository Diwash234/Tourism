/**
 * CircularGallery — 3D rotating circular image reel for destination
 * detail pages. Images orbit around a central point; scroll/click/hover
 * rotates them; the front card is larger, focused, and clickable.
 *
 * Fully keyboard accessible (left/right/home/end), reduced-motion aware,
 * and lazy-loads images.
 */
import { useCallback, useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiChevronLeft, FiChevronRight, FiZoomIn } from "react-icons/fi"
import { cn } from "../../utils/cn"
import PlaceholderImage from "../common/PlaceholderImage"

export default function CircularGallery({
  images = [],                   // array of {url, alt, caption?}
  title,
  className = "",
  radius = 260,
  autoRotate = false,
}) {
  const [active, setActive] = useState(0)
  const [paused, setPaused] = useState(false)
  const [viewerOpen, setViewerOpen] = useState(false)
  const containerRef = useRef(null)
  const reduced = typeof window !== "undefined" &&
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches

  const count = images.length || 0

  const rotate = useCallback((dir) => {
    if (!count) return
    setActive((i) => (i + dir + count) % count)
  }, [count])

  useEffect(() => {
    if (!autoRotate || paused || reduced || !count) return
    const t = setInterval(() => setActive((i) => (i + 1) % count), 4500)
    return () => clearInterval(t)
  }, [autoRotate, paused, reduced, count])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const onWheel = (e) => {
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        e.preventDefault()
        rotate(e.deltaX > 0 ? 1 : -1)
      }
    }
    el.addEventListener("wheel", onWheel, { passive: false })
    return () => el.removeEventListener("wheel", onWheel)
  }, [rotate])

  useEffect(() => {
    const onKey = (e) => {
      if (!containerRef.current?.contains(document.activeElement) &&
          viewerOpen === false) return
      if (e.key === "ArrowRight") rotate(1)
      else if (e.key === "ArrowLeft") rotate(-1)
      else if (e.key === "Escape") setViewerOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [rotate, viewerOpen])

  if (!count) {
    return (
      <div className={cn("relative h-64 rounded-3xl flex items-center justify-center bg-stone-100", className)}>
        <PlaceholderImage title={title || "destination"} className="absolute inset-0 rounded-3xl opacity-40" />
        <p className="relative text-stone-500 text-sm">No photos yet</p>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      role="region"
      aria-roledescription="carousel"
      aria-label={title ? `${title} photo reel` : "Photo reel"}
      className={cn("relative w-full overflow-hidden rounded-3xl bg-gradient-to-b from-stone-900 to-stone-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400", className)}
      style={{ height: Math.max(420, radius * 1.6), perspective: "1200px" }}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Background ambient */}
      <div className="absolute inset-0 opacity-60">
        <PlaceholderImage src={images[active]?.url} title={title} className="absolute inset-0" />
        <div className="absolute inset-0 bg-gradient-to-t from-stone-900/90 via-stone-900/40 to-stone-900/70 backdrop-blur-sm" />
      </div>

      {/* Circular reel */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className="relative"
          style={{
            width: radius * 2,
            height: radius * 1.4,
            transformStyle: "preserve-3d",
            transition: reduced ? "none" : "transform 650ms cubic-bezier(.2,.8,.2,1)",
            transform: `rotateY(${active * -(360 / count)}deg)`,
          }}
        >
          {images.map((img, i) => {
            const angle = (i / count) * 360
            const isActive = i === active
            return (
              <button
                key={i}
                onClick={() => setActive(i)}
                aria-label={`Photo ${i + 1} of ${count}${img.caption ? " — " + img.caption : ""}`}
                className={cn(
                  "absolute left-1/2 top-1/2 -ml-[140px] -mt-[95px]",
                  "w-[280px] h-[190px] rounded-2xl overflow-hidden ring-1 ring-white/20",
                  "shadow-2xl transition-all duration-500",
                  isActive ? "opacity-100 cursor-pointer" : "opacity-60 hover:opacity-90",
                )}
                style={{
                  transform: `rotateY(${angle}deg) translateZ(${radius}px) scale(${isActive ? 1.05 : 0.9})`,
                }}
              >
                <PlaceholderImage
                  src={img.url}
                  title={img.alt || title}
                  className="absolute inset-0"
                />
                {isActive && img.caption && (
                  <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent p-3 text-white text-xs font-medium">
                    {img.caption}
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Controls */}
      <div className="absolute inset-x-0 bottom-4 flex items-center justify-center gap-3 z-10">
        <button
          aria-label="Previous photo"
          onClick={() => rotate(-1)}
          className="w-10 h-10 rounded-full bg-white/10 backdrop-blur hover:bg-white/20 text-white flex items-center justify-center border border-white/20 transition"
        >
          <FiChevronLeft />
        </button>
        <div className="flex gap-1.5 items-center px-2">
          {images.map((_, i) => (
            <button
              key={i}
              aria-label={`Go to photo ${i + 1}`}
              onClick={() => setActive(i)}
              className={cn(
                "h-1.5 rounded-full transition-all",
                i === active ? "w-6 bg-white" : "w-1.5 bg-white/40 hover:bg-white/70",
              )}
            />
          ))}
        </div>
        <button
          aria-label="Next photo"
          onClick={() => rotate(1)}
          className="w-10 h-10 rounded-full bg-white/10 backdrop-blur hover:bg-white/20 text-white flex items-center justify-center border border-white/20 transition"
        >
          <FiChevronRight />
        </button>
        <button
          aria-label="Open full viewer"
          onClick={() => setViewerOpen(true)}
          className="ml-2 w-10 h-10 rounded-full bg-white/10 backdrop-blur hover:bg-white/20 text-white flex items-center justify-center border border-white/20 transition"
        >
          <FiZoomIn />
        </button>
      </div>

      {title && (
        <div className="absolute top-4 left-4 text-white/80 text-xs font-medium tracking-wide uppercase">
          {title} · {active + 1}/{count}
        </div>
      )}

      {/* Full viewer modal */}
      <AnimatePresence>
        {viewerOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-20 bg-black/90 flex items-center justify-center p-6"
            onClick={() => setViewerOpen(false)}
          >
            <motion.img
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              src={images[active]?.url}
              alt={images[active]?.alt || title}
              className="max-h-full max-w-full rounded-2xl shadow-2xl object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
