import { Link } from 'react-router-dom'
import { FiChevronRight, FiHome } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Breadcrumb component that adapts to different screen sizes.
 * - Mobile: Compact breadcrumb with ellipsis
 * - Tablet/Desktop: Full breadcrumb with all items
 */
const ResponsiveBreadcrumb = ({
  items,
  className = '',
}) => {
  const { isMobile } = useResponsive()

  // Mobile: Show only last 2 items
  const displayItems = isMobile ? items.slice(-2) : items

  return (
    <nav aria-label="Breadcrumb" className={className}>
      <ol className="flex items-center gap-1 text-sm">
        {/* Home icon for mobile */}
        {isMobile && items.length > 2 && (
          <li>
            <Link
              to="/"
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Home"
            >
              <FiHome className="w-4 h-4" />
            </Link>
          </li>
        )}

        {isMobile && items.length > 2 && (
          <li className="text-gray-400">
            <FiChevronRight className="w-4 h-4" />
          </li>
        )}

        {displayItems.map((item, index) => {
          const isLast = index === displayItems.length - 1

          return (
            <li key={index} className="flex items-center gap-1">
              {index > 0 && (
                <FiChevronRight className="w-4 h-4 text-gray-400" />
              )}
              {isLast ? (
                <span
                  className={`font-medium text-gray-900 dark:text-gray-100 ${
                    isMobile ? 'text-sm' : 'text-sm'
                  }`}
                  aria-current="page"
                >
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.path}
                  className={`text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 ${
                    isMobile ? 'text-sm' : 'text-sm'
                  }`}
                >
                  {item.label}
                </Link>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export default ResponsiveBreadcrumb
