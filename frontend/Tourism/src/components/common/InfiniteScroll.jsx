import { useState, useEffect, useCallback } from "react"
import { FiRefreshCw } from "react-icons/fi"

/**
 * Infinite scroll component that loads more content when the user
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
  const [isLoading, setIsLoading] = useState(false)

  const handleScroll = useCallback(() => {
    if (isLoading || loading || !hasMore) return

    const scrollTop = window.scrollY
    const docHeight = document.documentElement.scrollHeight
    const winHeight = window.innerHeight

    if (scrollTop + winHeight >= docHeight - threshold) {
      setIsLoading(true)
      onLoadMore?.().finally(() => setIsLoading(false))
    }
  }, [isLoading, loading, hasMore, threshold, onLoadMore])

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [handleScroll])

  return (
    <div className={className}>
      {children}
      {(isLoading || loading) && (
        <div className="flex items-center justify-center py-8">
          <FiRefreshCw className="animate-spin text-[var(--ny-green)]" size={24} />
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">Loading more...</span>
        </div>
      )}
      {!hasMore && (
        <div className="text-center py-8">
          <p className="text-sm text-gray-400 dark:text-gray-500">No more content to load</p>
        </div>
      )}
    </div>
  )
}
