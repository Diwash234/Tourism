import { FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Pagination component that adapts to different screen sizes.
 * - Mobile: Compact pagination with prev/next only
 * - Tablet/Desktop: Full pagination with page numbers
 */
const ResponsivePagination = ({
  currentPage,
  totalPages,
  onPageChange,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  const getVisiblePages = () => {
    if (isMobile) {
      return [currentPage]
    }

    const pages = []
    const start = Math.max(1, currentPage - 2)
    const end = Math.min(totalPages, currentPage + 2)

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    return pages
  }

  const visiblePages = getVisiblePages()

  return (
    <nav className={`flex items-center justify-center gap-2 ${className}`} aria-label="Pagination">
      {/* Previous */}
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={`flex items-center justify-center ${isMobile ? 'w-10 h-10' : 'w-10 h-10'} rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed`}
        aria-label="Previous page"
      >
        <FiChevronLeft className="w-5 h-5" />
      </button>

      {/* Page Numbers */}
      {!isMobile && visiblePages[0] > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            1
          </button>
          {visiblePages[0] > 2 && <span className="px-2 text-gray-500">...</span>}
        </>
      )}

      {visiblePages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`${
            isMobile ? 'w-10 h-10' : 'w-10 h-10'
          } rounded-lg border ${
            page === currentPage
              ? 'bg-emerald-600 border-emerald-600 text-white'
              : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          }`}
          aria-current={page === currentPage ? 'page' : undefined}
        >
          {page}
        </button>
      ))}

      {!isMobile && visiblePages[visiblePages.length - 1] < totalPages && (
        <>
          {visiblePages[visiblePages.length - 1] < totalPages - 1 && (
            <span className="px-2 text-gray-500">...</span>
          )}
          <button
            onClick={() => onPageChange(totalPages)}
            className="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {totalPages}
          </button>
        </>
      )}

      {/* Next */}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={`flex items-center justify-center ${isMobile ? 'w-10 h-10' : 'w-10 h-10'} rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed`}
        aria-label="Next page"
      >
        <FiChevronRight className="w-5 h-5" />
      </button>
    </nav>
  )
}

export default ResponsivePagination
