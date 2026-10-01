import { useEffect, useCallback, useRef } from "react"
import LoadingSpinner from "./LoadingSpinner"

/**
 * Infinite scroll component — loads more content when the user
 * scrolls near the bottom of the page.
 */
export default function InfiniteScroll({
  children,
  hasMore,
  onLoadMore,
  loading = false,
  threshold = 200,
  className = "",
}) {
  const observerRef = useRef(null)
  const loadMoreRef = useRef(null)

  const handleObserver = useCallback(
    (entries) => {
      const [target] = entries
      if (target.isIntersecting && hasMore && !loading) {
        onLoadMore?.()
      }
    },
    [hasMore, loading, onLoadMore]
  )

  useEffect(() => {
    const element = loadMoreRef.current
    if (!element) return undefined

    observerRef.current = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: `${threshold}px`,
      threshold: 0,
    })

    observerRef.current.observe(element)
    return () => observerRef.current?.disconnect()
  }, [handleObserver, threshold])

  return (
    <div className={className}>
      {children}
      <div ref={loadMoreRef} className="flex justify-center py-6">
        {loading && <LoadingSpinner size="md" label="Loading more..." />}
        {!hasMore && !loading && (
          <p className="text-sm text-gray-400 dark:text-gray-500">No more content to load</p>
        )}
      </div>
    </div>
  )
}
