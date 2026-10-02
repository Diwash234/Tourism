import { FiGrid, FiList } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive View Toggle component for switching between grid and list views.
 * - Mobile: Icon-only toggle
 * - Tablet/Desktop: Icon + label toggle
 */
const ResponsiveViewToggle = ({
  view,
  onViewChange,
  gridLabel = 'Grid',
  listLabel = 'List',
  className = '',
}) => {
  const { isMobile } = useResponsive()

  return (
    <div className={`flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 ${className}`}>
      <button
        onClick={() => onViewChange('grid')}
        className={`flex items-center gap-2 ${isMobile ? 'p-2' : 'px-3 py-1.5'} rounded-md transition-colors ${
          view === 'grid'
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
        }`}
        aria-label={`View as ${gridLabel}`}
        aria-pressed={view === 'grid'}
      >
        <FiGrid className="w-4 h-4" />
        {!isMobile && <span className="text-sm">{gridLabel}</span>}
      </button>
      <button
        onClick={() => onViewChange('list')}
        className={`flex items-center gap-2 ${isMobile ? 'p-2' : 'px-3 py-1.5'} rounded-md transition-colors ${
          view === 'list'
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
        }`}
        aria-label={`View as ${listLabel}`}
        aria-pressed={view === 'list'}
      >
        <FiList className="w-4 h-4" />
        {!isMobile && <span className="text-sm">{listLabel}</span>}
      </button>
    </div>
  )
}

export default ResponsiveViewToggle
