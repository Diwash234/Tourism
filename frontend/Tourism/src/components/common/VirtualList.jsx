import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Virtual List component for rendering large lists efficiently.
 * Only renders visible items, improving performance on all devices.
 */
const VirtualList = ({
  items,
  itemHeight,
  renderItem,
  overscan = 5,
  className = '',
  containerHeight = 600,
}) => {
  const containerRef = useRef(null)
  const [scrollTop, setScrollTop] = useState(0)
  const [containerSize, setContainerSize] = useState({ width: 0, height: containerHeight })

  useEffect(() => {
    const element = containerRef.current
    if (!element) return

    const resizeObserver = new ResizeObserver((entries) => {
      const [entry] = entries
      setContainerSize({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      })
    })

    resizeObserver.observe(element)
    return () => resizeObserver.disconnect()
  }, [])

  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop)
  }, [])

  // Calculate visible range
  const totalHeight = items.length * itemHeight
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
  const endIndex = Math.min(
    items.length,
    Math.ceil((scrollTop + containerSize.height) / itemHeight) + overscan
  )

  // Calculate offset
  const offsetY = startIndex * itemHeight

  // Get visible items
  const visibleItems = items.slice(startIndex, endIndex)

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            transform: `translateY(${offsetY}px)`,
          }}
        >
          {visibleItems.map((item, index) => (
            <div key={startIndex + index} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default VirtualList
