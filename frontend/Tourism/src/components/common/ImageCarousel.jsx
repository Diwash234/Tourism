import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiChevronLeft, FiChevronRight } from "react-icons/fi"

export default function ImageCarousel({ images = [], autoPlay = true, interval = 5000, height = "400px" }) {
  const [currentIdx, setCurrentIdx] = useState(0)

  useEffect(() => {
    if (!autoPlay || images.length <= 1) return
    const timer = setInterval(() => {
      setCurrentIdx((prev) => (prev === images.length - 1 ? 0 : prev + 1))
    }, interval)
    return () => clearInterval(timer)
  }, [autoPlay, images.length, interval])

  if (!images || images.length === 0) return null

  return (
    <div className="relative rounded-3xl overflow-hidden shadow-2xl bg-black group" style={{ height }}>
      <AnimatePresence mode="wait">
        <motion.img
          key={currentIdx}
          src={images[currentIdx]}
          alt={`Slide ${currentIdx + 1}`}
          initial={{ opacity: 0, scale: 1.05 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full h-full object-cover"
        />
      </AnimatePresence>

      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none" />

      {images.length > 1 && (
        <>
          <button
            onClick={() => setCurrentIdx((p) => (p === 0 ? images.length - 1 : p - 1))}
            className="absolute left-3 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/40 hover:bg-black/80 text-white backdrop-blur transition-all opacity-0 group-hover:opacity-100"
          >
            <FiChevronLeft size={20} />
          </button>
          <button
            onClick={() => setCurrentIdx((p) => (p === images.length - 1 ? 0 : p + 1))}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/40 hover:bg-black/80 text-white backdrop-blur transition-all opacity-0 group-hover:opacity-100"
          >
            <FiChevronRight size={20} />
          </button>

          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
            {images.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentIdx(i)}
                className={`h-2 rounded-full transition-all ${
                  currentIdx === i ? "w-6 bg-amber-400" : "w-2 bg-white/50 hover:bg-white"
                }`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
