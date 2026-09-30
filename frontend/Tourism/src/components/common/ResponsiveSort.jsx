import { useState } from 'react'
import { FiChevronDown } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Sort component that adapts to different screen sizes.
 * - Mobile: Dropdown select
 * - Tablet/Desktop: Inline sort buttons
 */
const ResponsiveSort = ({
  value,
  onChange,
  options,
  label = 'Sort by',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const { isMobile } = useResponsive()

  const selectedOption = options.find((opt) => opt.value === value)

  // Mobile: Dropdown
  if (isMobile) {
    return (
      <div className={`relative ${className}`}>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-gray-100 appearance-none"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <FiChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>
    )
  }

  // Desktop: Inline buttons
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-sm text-gray-500 dark:text-gray-400">{label}:</span>
      <div className="flex gap-1">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              value === option.value
                ? 'bg-emerald-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default ResponsiveSort
