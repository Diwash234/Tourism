import { useState, useEffect, useCallback, useRef } from "react"
import { FiChevronLeft, FiChevronRight } from "react-icons/fi"

/**
 * Accessible carousel with keyboard navigation, touch swipe support,
 * autoplay, and dot indicators.
 */
export default function Carousel({
  children,
  autoPlay = false,
  interval = 5000,
  showDots = true,
  showArrows = true,
  className = "",
}) {
  const [current, setCurrent] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const touchStartX = useRef(0)
  const touchEndX = useRef(0)
  const count = Array.isArray(children) ? children.length : 1

  const goTo = useCallback((index) => {
    setCurrent(((index % count) + count) % count)
  }, [count])

  const goNext = useCallback(() => goTo(current + 1), [current, goTo])
  const goPrev = useCallback(() => goTo(current - 1), [current, goTo])

  useEffect(() => {
    if (!autoPlay || isPaused || count <= 1) return undefined
    const timer = setInterval(goNext, interval)
    return () => clearInterval(timer)
  }, [autoPlay, isPaused, interval, goNext, count])

  const handleKeyDown = (e) => {
    if (e.key === "ArrowLeft") { e.preventDefault(); goPrev() }
    if (e.key === "ArrowRight") { e.preventDefault(); goNext() }
  }

  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX
  }

  const handleTouchMove = (e) => {
    touchEndX.current = e.touches[0].clientX
  }

  const handleTouchEnd = () => {
    const diff = touchStartX.current - touchEndX.current
    if (Math.abs(diff) > 50) {
      if (diff > 0) goNext()
      else goPrev()
    }
  }

  return (
    <div
      className={`relative overflow-hidden ${className}`}
      role="region"
      aria-roledescription="carousel"
      aria-label="Image carousel"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div
        className="flex transition-transform duration-500 ease-out"
        style={{ transform: `translateX(-${current * 100}%)` }}
      >
        {Array.isArray(children)
          ? children.map((child, i) => (
              <div key={i} className="w-full flex-shrink-0" role="group" aria-roledescription="slide" aria-label={`${i + 1} of ${count}`}>
                {child}
              </div>
            ))
          : <div className="w-full flex-shrink-0">{children}</div>
        }
      </div>

      {showArrows && count > 1 && (
        <>
          <button
            type="button"
            onClick={goPrev}
            className="absolute left-2 top-1/2 -translate-y-1/2 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm hover:bg-black/60 transition-colors"
            aria-label="Previous slide"
          >
            <FiChevronLeft size={20} />
          </button>
          <button
            type="button"
            onClick={goNext}
            className="absolute right-2 top-1/2 -translate-y-1/2 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur-sm hover:bg-black/60 transition-colors"
            aria-label="Next slide"
          >
            <FiChevronRight size={20} />
          </button>
        </>
      )}

      {showDots && count > 1 && (
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2">
          {Array.from({ length: count }).map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => goTo(i)}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === current ? "w-6 bg-white" : "w-2 bg-white/50 hover:bg-white/75"
              }`}
              aria-label={`Go to slide ${i + 1}`}
              aria-current={i === current ? "true" : undefined}
            />
          ))}
        </div>
      )}
    </div>
  )
}
