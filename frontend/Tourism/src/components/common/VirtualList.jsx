import { useState, useEffect, useRef, useCallback } from "react"

/**
 * Virtual list component — efficiently renders large lists by only
 * rendering visible items. Useful for destination lists with thousands of items.
 */
export default function VirtualList({
  items = [],
  itemHeight = 80,
  overscan = 5,
  renderItem,
  className = "",
  containerHeight = 600,
}) {
  const containerRef = useRef(null)
  const [scrollTop, setScrollTop] = useState(0)

  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop)
  }, [])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return undefined
    container.addEventListener("scroll", handleScroll, { passive: true })
    return () => container.removeEventListener("scroll", handleScroll)
  }, [handleScroll])

  const totalHeight = items.length * itemHeight
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
  const endIndex = Math.min(
    items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  )

  const visibleItems = items.slice(startIndex, endIndex)

  return (
    <div
      ref={containerRef}
      className={`overflow-y-auto ${className}`}
      style={{ height: containerHeight }}
    >
      <div style={{ height: totalHeight, position: "relative" }}>
        {visibleItems.map((item, i) => (
          <div
            key={item.id || startIndex + i}
            style={{
              position: "absolute",
              top: (startIndex + i) * itemHeight,
              left: 0,
              right: 0,
              height: itemHeight,
            }}
          >
            {renderItem(item, startIndex + i)}
          </div>
        ))}
      </div>
    </div>
  )
}
