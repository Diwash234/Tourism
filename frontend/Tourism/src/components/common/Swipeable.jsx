import { useState, useRef } from 'react'

/**
 * Swipeable component for touch-enabled swipe gestures.
 * Works on mobile and tablet devices.
 */
const Swipeable = ({
  children,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  className = '',
}) => {
  const [touchStart, setTouchStart] = useState(null)
  const [touchEnd, setTouchEnd] = useState(null)
  const [swiping, setSwiping] = useState(false)
  const containerRef = useRef(null)

  const handleTouchStart = (e) => {
    setTouchEnd(null)
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    })
    setSwiping(true)
  }

  const handleTouchMove = (e) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    })
  }

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) {
      setSwiping(false)
      return
    }

    const deltaX = touchStart.x - touchEnd.x
    const deltaY = touchStart.y - touchEnd.y
    const absDeltaX = Math.abs(deltaX)
    const absDeltaY = Math.abs(deltaY)

    // Determine swipe direction
    if (absDeltaX > absDeltaY && absDeltaX > threshold) {
      // Horizontal swipe
      if (deltaX > 0 && onSwipeLeft) {
        onSwipeLeft()
      } else if (deltaX < 0 && onSwipeRight) {
        onSwipeRight()
      }
    } else if (absDeltaY > absDeltaX && absDeltaY > threshold) {
      // Vertical swipe
      if (deltaY > 0 && onSwipeUp) {
        onSwipeUp()
      } else if (deltaY < 0 && onSwipeDown) {
        onSwipeDown()
      }
    }

    setTouchStart(null)
    setTouchEnd(null)
    setSwiping(false)
  }

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className={`${className} ${swiping ? 'select-none' : ''}`}
      style={{ touchAction: 'pan-y' }}
    >
      {children}
    </div>
  )
}

export default Swipeable
