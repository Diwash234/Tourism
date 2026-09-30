import { useState } from 'react'
import { FiFilter, FiX } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Filter component that adapts to different screen sizes.
 * - Mobile: Bottom sheet filter panel
 * - Tablet/Desktop: Sidebar filter panel
 */
const ResponsiveFilter = ({
  filters,
  onFilterChange,
  onClear,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const { isMobile } = useResponsive()

  const activeFilters = Object.values(filters).filter(Boolean).length

  const filterContent = (
    <div className="space-y-4">
      {Object.entries(filters).map(([key, filter]) => (
        <div key={key}>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {filter.label}
          </label>
          {filter.type === 'select' ? (
            <select
              value={filter.value || ''}
              onChange={(e) => onFilterChange(key, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="">All</option>
              {filter.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : filter.type === 'range' ? (
            <div className="flex gap-2">
              <input
                type="number"
                value={filter.value?.[0] || ''}
                onChange={(e) => onFilterChange(key, [e.target.value, filter.value?.[1]])}
                placeholder="Min"
                className="w-1/2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
              />
              <input
                type="number"
                value={filter.value?.[1] || ''}
                onChange={(e) => onFilterChange(key, [filter.value?.[0], e.target.value])}
                placeholder="Max"
                className="w-1/2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
              />
            </div>
          ) : (
            <input
              type="text"
              value={filter.value || ''}
              onChange={(e) => onFilterChange(key, e.target.value)}
              placeholder={filter.placeholder}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
            />
          )}
        </div>
      ))}

      {activeFilters > 0 && (
        <button
          onClick={onClear}
          className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
        >
          Clear all filters
        </button>
      )}
    </div>
  )

  // Mobile: Bottom sheet
  if (isMobile) {
    return (
      <>
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <FiFilter className="w-4 h-4" />
          Filters
          {activeFilters > 0 && (
            <span className="w-5 h-5 bg-emerald-600 text-white text-xs rounded-full flex items-center justify-center">
              {activeFilters}
            </span>
          )}
        </button>

        {isOpen && (
          <div className="fixed inset-0 z-50">
            <div className="fixed inset-0 bg-black/50" onClick={() => setIsOpen(false)} />
            <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 rounded-t-xl p-4 max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Filters</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-gray-400 hover:text-gray-600"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>
              {filterContent}
              <button
                onClick={() => setIsOpen(false)}
                className="w-full mt-4 px-4 py-3 bg-emerald-600 text-white rounded-lg font-medium"
              >
                Apply Filters
              </button>
            </div>
          </div>
        )}
      </>
    )
  }

  // Desktop: Sidebar
  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <FiFilter className="w-5 h-5" />
        Filters
      </h3>
      {filterContent}
    </div>
  )
}

export default ResponsiveFilter
