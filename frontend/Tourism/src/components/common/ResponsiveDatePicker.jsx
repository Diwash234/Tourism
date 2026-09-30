import { useState } from 'react'
import { FiCalendar } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Date Picker component that adapts to different screen sizes.
 * - Mobile: Native date input
 * - Tablet/Desktop: Custom date picker with calendar popup
 */
const ResponsiveDatePicker = ({
  value,
  onChange,
  placeholder = 'Select date',
  minDate,
  maxDate,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const { isMobile } = useResponsive()

  // Mobile: Use native date input
  if (isMobile) {
    return (
      <div className={`relative ${className}`}>
        <FiCalendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="date"
          value={value ? new Date(value).toISOString().split('T')[0] : ''}
          onChange={(e) => onChange(e.target.value ? new Date(e.target.value) : null)}
          min={minDate}
          max={maxDate}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
        />
      </div>
    )
  }

  // Desktop: Custom date picker
  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100 text-left"
      >
        <FiCalendar className="w-5 h-5 text-gray-400" />
        <span className={value ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400'}>
          {value ? new Date(value).toLocaleDateString() : placeholder}
        </span>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute z-50 mt-2 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg p-4 min-w-[280px]">
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => setIsOpen(false)}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Cancel
              </button>
              <span className="font-medium">Select Date</span>
              <button
                onClick={() => setIsOpen(false)}
                className="text-sm text-emerald-600 hover:text-emerald-700"
              >
                Done
              </button>
            </div>
            <input
              type="date"
              value={value ? new Date(value).toISOString().split('T')[0] : ''}
              onChange={(e) => onChange(e.target.value ? new Date(e.target.value) : null)}
              min={minDate}
              max={maxDate}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>
        </>
      )}
    </div>
  )
}

export default ResponsiveDatePicker
