import { useState, useRef, useCallback } from 'react'
import { Spinner } from './LoadingStates'

/**
 * Pull to Refresh component for mobile and tablet devices.
 * Provides visual feedback during refresh.
 */
const PullToRefresh = ({
  onRefresh,
  children,
  threshold = 80,
  className = '',
}) => {
  const [pullDistance, setPullDistance] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const [startY, setStartY] = useState(0)
  const containerRef = useRef(null)

  const handleTouchStart = useCallback((e) => {
    if (refreshing) return
    if (containerRef.current && containerRef.current.scrollTop === 0) {
      setStartY(e.touches[0].clientY)
    }
  }, [refreshing])

  const handleTouchMove = useCallback((e) => {
    if (refreshing || startY === 0) return

    const currentY = e.touches[0].clientY
    const diff = currentY - startY

    if (diff > 0 && containerRef.current && containerRef.current.scrollTop === 0) {
      // Add resistance
      const resistance = 0.5
      setPullDistance(Math.min(diff * resistance, threshold * 1.5))
    }
  }, [refreshing, startY, threshold])

  const handleTouchEnd = useCallback(async () => {
    if (refreshing) return

    if (pullDistance >= threshold) {
      setRefreshing(true)
      try {
        await onRefresh()
      } finally {
        setRefreshing(false)
        setPullDistance(0)
        setStartY(0)
      }
    } else {
      setPullDistance(0)
      setStartY(0)
    }
  }, [pullDistance, refreshing, onRefresh, threshold])

  const getIndicatorStyle = () => {
    if (pullDistance === 0) return { opacity: 0 }
    if (pullDistance < threshold) return { opacity: 0.5 }
    return { opacity: 1 }
  }

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className={`relative overflow-auto ${className}`}
    >
      {/* Pull indicator */}
      <div
        className="absolute left-0 right-0 flex justify-center transition-all duration-200"
        style={{
          top: pullDistance - 40,
          ...getIndicatorStyle(),
        }}
      >
        <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-full shadow-lg">
          {refreshing ? (
            <>
              <Spinner size="sm" />
              <span className="text-sm font-medium">Refreshing...</span>
            </>
          ) : pullDistance >= threshold ? (
            <span className="text-sm font-medium text-emerald-600">Release to refresh</span>
          ) : (
            <span className="text-sm font-medium text-gray-500">Pull to refresh</span>
          )}
        </div>
      </div>

      {/* Content */}
      <div
        style={{
          transform: `translateY(${pullDistance}px)`,
          transition: refreshing || pullDistance === 0 ? 'transform 0.3s ease' : 'none',
        }}
      >
        {children}
      </div>
    </div>
  )
}

export default PullToRefresh
