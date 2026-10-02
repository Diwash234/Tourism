import { useState, useRef, useEffect } from 'react'
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Carousel component that adapts to different screen sizes.
 * - Mobile: Swipeable carousel with touch support
 * - Tablet/Desktop: Arrow navigation with hover effects
 */
const ResponsiveCarousel = ({
  children,
  autoPlay = false,
  autoPlayInterval = 5000,
  showDots = true,
  showArrows = true,
  className = '',
}) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [startX, setStartX] = useState(0)
  const [translateX, setTranslateX] = useState(0)
  const containerRef = useRef(null)
  const { isMobile } = useResponsive()

  const items = Array.isArray(children) ? children : [children]
  const itemCount = items.length

  // Auto-play
  useEffect(() => {
    if (!autoPlay || itemCount <= 1) return

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % itemCount)
    }, autoPlayInterval)

    return () => clearInterval(interval)
  }, [autoPlay, autoPlayInterval, itemCount])

  const goToSlide = (index) => {
    setCurrentIndex(index)
  }

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : itemCount - 1))
  }

  const goToNext = () => {
    setCurrentIndex((prev) => (prev < itemCount - 1 ? prev + 1 : 0))
  }

  // Touch handlers for mobile swipe
  const handleTouchStart = (e) => {
    setIsDragging(true)
    setStartX(e.touches[0].clientX)
  }

  const handleTouchMove = (e) => {
    if (!isDragging) return
    const currentX = e.touches[0].clientX
    const diff = currentX - startX
    setTranslateX(diff)
  }

  const handleTouchEnd = () => {
    if (!isDragging) return

    const threshold = 50
    if (translateX > threshold) {
      goToPrevious()
    } else if (translateX < -threshold) {
      goToNext()
    }

    setIsDragging(false)
    setTranslateX(0)
  }

  if (itemCount === 0) return null

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {/* Carousel container */}
      <div
        ref={containerRef}
        className="flex transition-transform duration-300"
        style={{
          transform: `translateX(calc(-${currentIndex * 100}% + ${translateX}px))`,
          transition: isDragging ? 'none' : 'transform 0.3s ease',
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {items.map((item, index) => (
          <div key={index} className="w-full flex-shrink-0">
            {item}
          </div>
        ))}
      </div>

      {/* Navigation arrows */}
      {showArrows && itemCount > 1 && (
        <>
          <button
            onClick={goToPrevious}
            className={`absolute top-1/2 -translate-y-1/2 ${
              isMobile ? 'left-2 w-10 h-10' : 'left-4 w-12 h-12'
            } bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-full flex items-center justify-center text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-800 shadow-lg transition-colors`}
            aria-label="Previous slide"
          >
            <FiChevronLeft className={isMobile ? 'w-5 h-5' : 'w-6 h-6'} />
          </button>
          <button
            onClick={goToNext}
            className={`absolute top-1/2 -translate-y-1/2 ${
              isMobile ? 'right-2 w-10 h-10' : 'right-4 w-12 h-12'
            } bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-full flex items-center justify-center text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-800 shadow-lg transition-colors`}
            aria-label="Next slide"
          >
            <FiChevronRight className={isMobile ? 'w-5 h-5' : 'w-6 h-6'} />
          </button>
        </>
      )}

      {/* Dots indicator */}
      {showDots && itemCount > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`rounded-full transition-all ${
                index === currentIndex
                  ? isMobile ? 'w-6 h-2 bg-emerald-500' : 'w-8 h-2 bg-emerald-500'
                  : isMobile ? 'w-2 h-2 bg-white/50' : 'w-2 h-2 bg-white/50'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default ResponsiveCarousel
